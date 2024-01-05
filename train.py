import pyfirmata
import tensorflow as tf
import numpy as np
from time import sleep
from cam import record
from collections import deque
import random
import cv2

# Define the environment
rpm_max = 161
wat_max = 10001
vel_max = 51

write_locatoin = "/Users/tarioyou/biking/isef_bike/mainoutput.txt"

board = pyfirmata.Arduino('/dev/cu.usbserial-110')  # port
board.digital[13].write(1)  # or write(0)

it = pyfirmata.util.Iterator(board)
it.start()

# motor a connections
enA1pin = 9
enA2pin = 10
in1pin = 8
in2pin = 7
# motor b connections
enB1pin = 2
enB2pin = 3
in3pin = 4
in4pin = 5

enA1 = board.get_pin(f"p:{enA1pin}:o")
enA2 = board.get_pin(f"p:{enA2pin}:o")
in1 = board.get_pin(f"d:{in1pin}:o")
in2 = board.get_pin(f"d:{in2pin}:o")
enB1 = board.get_pin(f"p:{enB1pin}:o")
enB2 = board.get_pin(f"p:{enB2pin}:o")
in3 = board.get_pin(f"d:{in3pin}:o")
in4 = board.get_pin(f"d:{in4pin}:o")


def slice(im, starty, startx, endy, endx):
    grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    grey = grey[startx:endx, starty:endy]
    return grey


def write_digitals(v1, v2, v3, v4):
    in1.write(v1)
    in2.write(v2)
    in3.write(v3)
    in4.write(v4)


def upshift(upshift_duration=.9):
    write_digitals(0, 1, 0, 0)
    sleep(upshift_duration)
    write_digitals(1, 0, 0, 0)
    sleep(upshift_duration)
    write_digitals(0, 0, 0, 0)


def downshift(downshift_duration=2):
    write_digitals(0, 0, 1, 0)
    sleep(downshift_duration)
    write_digitals(0, 0, 0, 1)
    sleep(downshift_duration)
    write_digitals(0, 0, 0, 0)


class BikeEnvironment:
    def __init__(self):
        v, w, r = record(write_locatoin)
        self.state = [v, w, r]

    def step(self, action):
        rpm, watts, speed = self.state
        action_string = ""
        if action == 0:  # upshift 1 gears
            upshift()
            action_string = "upshift"
        elif action == 1:  # maintain current gear
            action_string = "maintain"
            pass
        elif action == 2:  # downshift 1 gear
            action_string = "downshift"
            downshift()
        else:
            print("wtf")
            quit()

        speed, watt, rpm = record(write_locatoin)

        # compute reward
        reward = speed - self.state[2]
        print(f'{reward=}\t{action_string=}')

        # update state
        self.state = np.array([rpm, watts, speed])

        return self.state, reward


class BikeAgent:
    def __init__(self, state_size, action_size, learning_rate=0.001, gamma=0.99, q_values=None):
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.9995

        # load previous q values
        if q_values is not None:
            self.q_values = np.load(q_values)
        else:
            self.q_values = np.zeros((rpm_max, wat_max, vel_max, action_size))

        self.model = self.build_model()
        self.replay_buffer = deque(maxlen=100000)

    def build_model(self):
        model = tf.keras.models.Sequential([
            tf.keras.layers.LSTM(
                128, input_dim=1, input_shape=(3, 1)),
            tf.keras.layers.Dense(64, activation='relu'),
            # tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(8, activation='relu'),
            tf.keras.layers.Dense(self.action_size, activation='linear')
        ])

        model.compile(loss='mse', optimizer=tf.keras.optimizers.Adam(
            lr=self.learning_rate))
        # print()
        # print(model.summary())
        # print()
        # quit()

        return model

    def act(self, state):
        # choose random action while limiting exploration
        if np.random.rand() <= self.epsilon:
            return np.random.choice(self.action_size)
        else:
            # if we dont want to explore ->
            # choose option that will maximize (exploit) our q values
            state = [int(s) for s in state]
            return np.argmax(self.q_values[state[0]][state[1]][state[2]][:])

    def learn(self, state, action, reward, next_state, i):
        state = [int(s) for s in state]
        next_state = [int(s) for s in next_state]

        self.replay_buffer.append((state, action, reward, next_state))

        batch_size = min(len(self.replay_buffer), 128)
        mini_batch = random.sample(self.replay_buffer, batch_size)

        for state, action, reward, next_state in mini_batch:
            q_value = self.q_values[state[0]][state[1]][state[2]][action]

            next_q = self.q_values[next_state[0]
                                   ][next_state[1]][next_state[2]][:]
            next_q_value = np.max(next_q)

            # gamma balance future reqrds - credit system (?)
            target = reward + self.gamma * next_q_value
            self.q_values[state[0]][state[1]][state[2]][action] = (
                1 - self.learning_rate) * q_value + self.learning_rate * target

            target_f = self.model.predict(np.array([state]))
            target_f[0][action] = target
            # input_data = state.reshape(-1, 1, 3)
            self.model.fit(np.array([state]),
                           target_f, epochs=20, verbose=0)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def save_q_values(self, filename):
        np.save(filename, self.q_values)


def train(env, agent, episodes=10000, max_steps=500, batch_size=32, load_model=None, save_freq=100):
    if load_model is not None:
        agent.model.load_weights(load_model)

    for episode in range(episodes):
        v, w, r = record(write_locatoin)
        state = [v, w, r]
        next_state = state
        sleep(0.2)
        score = 0

        coounter = 0

        while True:
            coounter += 1
            # current state = previous state
            state = next_state

            # random action based on previous state
            action = agent.act(state)

            # update current state
            v, w, r = record(write_locatoin)
            next_state = [v, w, r]

            # gets reward
            next_state, reward = env.step(action)

            # agent learn from reward
            agent.learn(state, action, reward, next_state, coounter)
            print(f'| {action=}\t{next_state=}\t{reward=}')

            if action != 0:
                sleep(2)

            state = next_state
            score += reward

            agent.save_q_values("q_values.npy")
            agent.model.save_weights("model_weights.h5")

    return agent


if __name__ == "__main__":
    env = BikeEnvironment()
    agent = BikeAgent(state_size=3, action_size=3,
                      learning_rate=0.001, gamma=0.99, q_values=None)  # q_values="q_values.npy"
    agent = train(env, agent, episodes=100, max_steps=500,
                  batch_size=128, load_model=None, save_freq=100)  # load_model="model_weights.h5"

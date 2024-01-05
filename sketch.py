import pyfirmata
from time import sleep

board = pyfirmata.Arduino('/dev/cu.usbserial-10')  # port
# board.digital[13].write(1) or write(0)

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


def write_digitals(v1, v2, v3, v4):
    in1.write(v1)
    in2.write(v2)
    in3.write(v3)
    in4.write(v4)


def directional_control():
    # set motors for max speed
    # pwm vals = 0 -> 255

    # turn on motors A and B
    write_digitals(1, 0, 1, 0)
    sleep(2)

    # change motor directions
    write_digitals(0, 1, 0, 1)
    sleep(2)

    # turn off motors
    write_digitals(0, 0, 0, 0)
    sleep(2)


def downshift(upshift_duration=.4):
    write_digitals(0, 1, 0, 0)
    sleep(upshift_duration)
    write_digitals(1, 0, 0, 0)
    sleep(upshift_duration)
    write_digitals(0, 0, 0, 0)


def upshift(downshift_duration=1):
    write_digitals(0, 0, 1, 0)
    sleep(downshift_duration)
    write_digitals(0, 0, 0, 1)
    sleep(downshift_duration)
    write_digitals(0, 0, 0, 0)


upshift(1.6)
downshift(.6)

# while True:
#     write_digitals(0, 0, 0, 0)
# # sleep(1)

# sleep(1)

# upshift(0.05)
# downshift(0.05)


'''
https://lastminuteengineers.com/l298n-dc-stepper-driver-arduino-tutorial/
'''

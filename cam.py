import cv2
import numpy as np
from mss import mss
import pytesseract

z = 84
v = [800, 1200, 1300, 1300]
w = [1300, 1868+z, 1608, 1902+z+20]
r = [1300, 1984+z, 1608, 2014+z+20]


def slice(im, starty, startx, endy, endx):
    grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    grey = grey[startx:endx, starty:endy]
    return grey


def read_number(img):
    # -c tessedit_char_whitelist=0123456789.
    cc = f'--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789.WRPMkm/'
    text = pytesseract.image_to_string(
        img, lang='eng', config=cc).replace('\n', '')
    return text


def record(write_location):
    monitor_number = 1
    sct = mss()

    mon = sct.monitors[monitor_number]

    print(mon)

    monitor = {
        "top": mon["top"],
        "left": mon["left"],
        "width": mon["left"] + mon["width"],
        "height": mon["top"] + mon["height"],
        "mon": monitor_number,
    }

    sct_img = sct.grab(monitor)  # (monitor)
    sct_img = np.array(sct_img)

    cv2.imwrite(f'/Users/tarioyou/biking/isef_bike/data/s.png', sct_img)

    # print(sct_img.shape)
    vel = slice(sct_img, v[0], v[1], v[2], v[3])
    wat = slice(sct_img, w[0], w[1], w[2], w[3])
    rpm = slice(sct_img, r[0], r[1], r[2], r[3])
    wat = cv2.bitwise_not(wat)
    rpm = cv2.bitwise_not(rpm)

    cv2.imwrite(f'/Users/tarioyou/biking/isef_bike/vel/vel.png', vel)
    cv2.imwrite(f'/Users/tarioyou/biking/isef_bike/rpm/rpm.png', rpm)
    cv2.imwrite(f'/Users/tarioyou/biking/isef_bike/wat/wat.png', wat)

    print(f'{read_number(vel).split(" ")[0]=}\t{
          read_number(wat)=}\t{read_number(rpm)=}')

    vel_num = read_number(vel).split()[0]
    wat_num = read_number(wat).replace('W', '')
    rpm_num = read_number(rpm).split()[0]

    vel_num = vel_num.split('.')[0]

    vel_num = int(vel_num)
    wat_num = int(wat_num)
    rpm_num = int(rpm_num)

    with open(write_location, 'a') as f:
        f.write(f'{vel_num=}\t{wat_num=}\t{rpm_num=}\n')

    return vel_num, wat_num, rpm_num

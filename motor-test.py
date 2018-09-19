from motorLib import Motor, time

motor = Motor("/dev/ttyAMA0")
# motor = Motor("/dev/ttyUSB0")

motor.setSpeed(1, 0.15)
motor.setSpeed(2, 0.15)
motor.setSpeed(3, 0.15)
for i in range(30):
    time.sleep(0.1)
#motor.closeMoveDeamon()
print(motor.getCnt())
motor.setSpeed(1, 0)
motor.setSpeed(2, 0)
motor.setSpeed(3, 0)

# 经测试，所有的电机都可以用，并且PWM正负与旋转计数的正负相对应

import serial, time, struct, threading, datetime, math

# 使用STM32驱动，检测3路磁编码，并受控输出PWM波形
# 经测试和文档查阅，转一圈输出1560个步进

class Motor:
    def __init__(self, port):  # port 可以是 "/dev/ttySx" 或是win上的COMx，若使用树莓派原生串口，则是/dev/ttyAMA0
        self.port = serial.Serial(port, baudrate=115200, bytesize=8, stopbits=1, timeout=2)
        self.pwmVal = 800  # 这个数值针对的是0529版本STM32控制器，可以自行更改
        self.alive = False
        self.x = 0
        self.y = 0
        self.theta = 0

    def setPIDspeed(self, channel, speed):  # pwm 为-1024到1024之间的浮点数，推荐使用500以下的
        if channel not in (1,2,3):
            return False
        speed = int(speed)
        if speed > 1023:
            speed = 1023
        if speed < -1023:
            speed = -1023
        direction = 0x00
        if speed < 0:
            direction = 0x10
            speed = -speed
        cmd1 = 0x0FF & ((channel << 6) | direction | 0x20 | (0x0F & (speed >> 6)))
        cmd2 = 0x03F & speed
        cmd = bytes((cmd1, cmd2))
        # print(cmd, len(cmd), "%x %x" % (cmd1, cmd2))
        self.port.write(cmd)

    def setSpeed(self, channel, pwm):  # pwm 为-1~1之间的浮点数，方向根据pwm正负自动调节
        if channel not in (1,2,3):
            return False
        if pwm > 1:
            pwm = 1
        if pwm < -1:
            pwm = -1
        direction = 0x10
        if pwm < 0:
            direction = 0x00
            pwm = -pwm
        pwmcnt = int(pwm * self.pwmVal)
        cmd1 = 0x0FF & ((channel << 6) | direction | (0x0F & (pwmcnt >> 6)))
        cmd2 = 0x03F & pwmcnt
        cmd = bytes((cmd1, cmd2))
        # print(cmd, len(cmd), "%x %x" % (cmd1, cmd2))
        self.port.write(cmd)
    
    # 如果使用deamon记录位移，请不要使用本函数，否则会造成数据缺失
    def getCnt(self):  # 整理本次到上次调用getCnt之间所有的数据
        cnt = self.port.inWaiting()
        if cnt == 0:
            return (0, 0, 0)
        data = self.port.read(cnt)
        chcnt = [0,0,0]
        for e in data:
            ch = 0x03 & (e >> 6)
            val = struct.unpack('b', bytes((0x0FF & (e << 2), )))[0] // 4
            # print(e, ch, val)
            if ch > 0:
                chcnt[ch-1] += val
        return tuple(chcnt)
    
    def startMoveDeamon(self, update = 0.1, hook = None):
        self.alive = True  # 关闭的时候需要设置这个
        self.okExit = threading.Event()
        self.thread_read = None
        self.update = update
        self.hook = hook
        self.thread_read = threading.Thread(target=self.MoveDeamon)
        self.thread_read.setDaemon(1)
        self.thread_read.start()

    def closeMoveDeamon(self):
        self.alive = False
        self.thread_read.join()
        self.thread_read = None

    # 经测量，轮子的直径为5.5cm（直径），轮子中心到地盘中心的距离为10.5cm（半径）
    # 以初始情况1号轮子方向为x轴，右手螺旋平面，z轴向上，确定y轴
    # theta方向为向上为正
    def _MoveGo(self, cntvar):
        kw = 0.000111  # vi = kw * (delta c / delta t)   vi = (pi*dw)/1560*(delta c / delta t), dw = 0.055, pi = 3.14
        deltax_natureaxis = kw / 1.732 * (cntvar[1] - cntvar[2])
        deltay_natureaxis = kw / (1 + 1.732) * ((cntvar[1] + cntvar[2]) / 2 - cntvar[0])
        deltat = - kw * (cntvar[0] + cntvar[1] + cntvar[2]) / 3 / 0.105
        theta = self.theta + deltat / 2  # 使用折中的角度计算位移
        deltax_absaxis = deltax_natureaxis * math.cos(theta) - deltay_natureaxis * math.sin(theta)
        deltay_absaxis = deltay_natureaxis * math.cos(theta) + deltax_natureaxis * math.sin(theta)

        self.theta += deltat
        self.x += deltax_absaxis
        self.y += deltay_absaxis

    def MoveDeamon(self):
        begin = datetime.datetime.now()
        cnt = [0, 0, 0]
        update = self.update
        hook = self.hook
        while self.alive:
            time.sleep(0.001)  # 位移必须粒度非常小，以保证位移的准确性
            timevar = (datetime.datetime.now() - begin).total_seconds()
            if timevar > update:
                if hook is not None:
                    hook(cnt, timevar)
                begin = datetime.datetime.now()
                cnt = [0, 0, 0]
            cntvar = self.getCnt()
            for i in range(3): cnt[i] += cntvar[i]  # 保存一下增量
            self._MoveGo(cntvar)  # 调用一下位移函数
        self.okExit.set()

    @staticmethod
    def hook_demo(cnt, timevar):
        speed = [0,0,0]
        for i in range(3): speed[i] = cnt[i] / timevar
        print(cnt, timevar, speed)


if __name__ == '__main__':
    motor = Motor("COM5")
    try:
        motor.setSpeed(1, -0.)
        #motor.port.read_all()
        #motor.startMoveDeamon(0.1, Motor.hook_demo)
        for i in range(10):
        #while True:
            time.sleep(0.1)
            # print(motor.getCnt())
        #motor.closeMoveDeamon()
        print(motor.getCnt())
    except KeyboardInterrupt:
        print(motor.getCnt())
        #motor.closeMoveDeamon()

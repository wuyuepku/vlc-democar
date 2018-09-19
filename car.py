#!/usr/bin/python3

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging, json, time, math
from libmotor import Motor
from optparse import OptionParser
app = Flask(__name__)
socketio = SocketIO()
socketio.init_app(app=app)
logging.getLogger('werkzeug').setLevel(logging.ERROR)  # 设置不输出GET请求之类的信息，只输出error，保证控制台干净

class CarObj(Motor):
    def __init__(self, serial=None):
        self.serial = serial
        if serial is not None:
            Motor.__init__(self, serial)  # call parent function
    
    def setspeed(self, vx, vy, w):  # vx:[-100,100] vy:[-100,100] w:[-100,100]
        print("setspeed vx:%d, vy:%d, w:%d" % (vx, vy, w))
        if self.serial is not None:
            v1 = w + vy
            v2 = w + math.sqrt(3)/2 * vx - vy/2
            v3 = w - math.sqrt(3)/2 * vx - vy/2
            self.setSpeed(1, v1/100.)
            self.setSpeed(2, v2/100.)
            self.setSpeed(3, v3/100.)
carobj = None

vx = 0
vy = 0
w = 0
def sendSpeedToUser():
    socketio.emit('speed', {
        "vx": vx,
        "vy": vy,
        "w": w
    }, broadcast=True)
def setspeed(speed):
    global vx
    global vy
    global w
    modified = False
    if 'vx' in speed:
        vx = speed['vx']
        modified = True
    if 'vy' in speed:
        vy = speed['vy']
        modified = True
    if 'w' in speed:
        w = speed['w']
        modified = True
    if modified:
        carobj.setspeed(vx, vy, w)

@app.route("/")
def index():
    return app.send_static_file('car.html')
@socketio.on('connect')
def ws_connect():
    print('socketio %s connect    at: %s' % (request.remote_addr, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
    sendSpeedToUser()
@socketio.on('disconnect')
def ws_disconnect():
    print('socketio %s disconnect at: %s' % (request.remote_addr, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
@socketio.on('setspeed')
def ws_setspeed(speed):
    print(speed)
    setspeed(speed)
    sendSpeedToUser()
play = {"mode": "square", "step": 0, "cnt": 0}
@socketio.on('setmode')
def ws_setmode(mode):
    print(mode)
    global play
    play["mode"] = mode
def timer50ms():
    global play
    if play["mode"] == "square":
        play["cnt"] += 1
        if play["cnt"] == 20:
            play["cnt"] = 0
            play["step"] = (play["step"] + 1) % 4
            v0 = 50
            if play["step"] == 0:
                setspeed({"vx": v0, "vy": 0})
                sendSpeedToUser()
            if play["step"] == 1:
                setspeed({"vx": 0, "vy": v0})
                sendSpeedToUser()
            if play["step"] == 2:
                setspeed({"vx": -v0, "vy": 0})
                sendSpeedToUser()
            if play["step"] == 3:
                setspeed({"vx": 0, "vy": -v0})
                sendSpeedToUser()
    elif play["mode"] == "circle":
        circle = 60  # 3s
        v0 = 80
        play["cnt"] += 1
        if play["cnt"] == circle:
            play["cnt"] = 0
        vx1 = v0 * math.cos(2 * math.pi / circle * play["cnt"])
        vy1 = v0 * math.sin(2 * math.pi / circle * play["cnt"])
        setspeed({"vx": vx1, "vy": vy1})
        sendSpeedToUser()
    else:
        play["step"] = 0
        play["cnt"] = 0
def bkgtask():
    while True:
        socketio.sleep(0.05)
        timer50ms()
socketio.start_background_task(bkgtask)

if __name__=='__main__':
    parser = OptionParser()
    parser.add_option("--host", type="string", dest="host", help="Server Host IP", default="0.0.0.0")
    parser.add_option("--port", type="int", dest="port", help="Server Host Port", default=8080)
    parser.add_option("--serial", type="string", dest="serial", help="Serial number", default="")
    options, args = parser.parse_args()
    print("\n\n##############################################")
    print("this will run on port %d of '%s'" % (options.port, options.host))
    carobj = CarObj(None if options.serial == "" else options.serial)
    print("serial is %s" % options.serial)
    print("##############################################\n\n")
    socketio.run(app, host=options.host, port=options.port)

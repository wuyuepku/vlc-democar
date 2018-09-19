#!/usr/bin/python3

"""
本程序为控制全向轮小车sensys VLC demo的程序
written by wy@180911
"""

import time, main, GUI
from optparse import OptionParser

def nowSettings():  # 用户想获取当前的系统信息，返回一个字典
    return {}

def userClickButton(button):  # 用户点击按钮事件
    print(button)

def userSyncSettings(settings):
    print(settings)

# flask服务器框架，本部分只包含通信，不包含任何逻辑
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import logging, json
app = Flask(__name__)
socketio = SocketIO()
socketio.init_app(app=app)
logging.getLogger('werkzeug').setLevel(logging.ERROR)  # 设置不输出GET请求之类的信息，只输出error，保证控制台干净

def maincall():
    global loopDelay
    GUI.log('main function start at: %s' % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    main.setup()
    GUI.log('setup finished at: %s' % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    while True:
        main.loop(main, socketio.sleep)
        socketio.sleep(main.loopDelay)

@app.route("/")
def index():
    return app.send_static_file('index.html')
@socketio.on('connect')
def ws_connect():
    GUI.log('socketio %s connect    at: %s' % (request.remote_addr, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
    sendSettingsToUser()
@socketio.on('disconnect')
def ws_disconnect():
    GUI.log('socketio %s disconnect at: %s' % (request.remote_addr, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())))
@socketio.on('button')
def ws_button(button):
    if button != "AutoTrig":  # to avoid lots of output log!
        GUI.log('user %s click button: %s' % (request.remote_addr, button))
    userClickButton(button)  # 逻辑层
    sendSettingsToUser()
@socketio.on('syncSettings')
def ws_syncSettings(settings):
    userSyncSettings(settings)
    sendSettingsToUser()
def sendSettingsToUser():
    settings = nowSettings()  # 逻辑层的事情
    socketio.emit('settings', settings, broadcast=True)
socketio.start_background_task(maincall)
def timerSendUpdatedStateToUsers():
    while True:
        socketio.sleep(0.3)
        if main.changed:
            main.changed = False
            sendSettingsToUser()
socketio.start_background_task(timerSendUpdatedStateToUsers)
if __name__=='__main__':
    parser = OptionParser()
    parser.add_option("--host", type="string", dest="host", help="Server Host IP", default="0.0.0.0")
    parser.add_option("--port", type="int", dest="port", help="Server Host Port", default=8080)
    options, args = parser.parse_args()
    GUI.registerSocketIO(socketio)  # enable GUI socketio
    print("\n\n##############################################")
    print("ArgosWebGui will run on port %d of '%s'" % (options.port, options.host))
    print("##############################################\n\n")
    socketio.run(app, host=options.host, port=options.port)
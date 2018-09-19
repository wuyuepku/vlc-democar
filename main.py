"""
this file exposes some variable and function to host.py, which host a web server

export variables:
    changed             # when any export varibles is modified, set this to True, and will be broadcast to all users
    loopDelay           # delay between one "loop()" end and next "loop()" begin, see loop() function below

export functions:
    setup()             # running all the time you wish to, it could be a loop to check
    loop()              # running all the time, you could check stream input/output, with delay
"""


loopDelay = 0.05  # for better robustness when continuous reading
version = "VLCdemocar v0.1"

changed = False
def changedF():  # when any export varible is modified, call this function
    global changed
    changed = True

def setup():
    pass

def loop(main, sleep):
    pass

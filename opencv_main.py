import numpy as np
import cv2
import sys
from flask import Flask, render_template, Response
from flask_basicauth import BasicAuth
import time
import threading
import argparse

from camera import VideoCamera
# from mail import EmailSender


# App Globals (do not edit)
email_update_interval = 3000 # sends an email only once in this time interval

object_classifier = cv2.CascadeClassifier("models/fullbody_recognition_model.xml") # an opencv classifier

video_camera = VideoCamera(flip=False, is_raspberry=True) # creates a camera object, flip vertically

email_sender = None

app = Flask(__name__)
basic_auth = BasicAuth(app)

last_epoch = 0
def check_for_objects():
    global last_epoch
    global email_sender
    while True:
        if (time.time() - last_epoch) > email_update_interval:
            last_epoch = time.time()
        else:
            time.sleep(3)
        # try:
        frame, found_obj = video_camera.get_object(object_classifier)
        if found_obj:
            print("Sending email...")
            # email_sender.sendEmail(frame)
            print("done!")
        # except:
        #     print("Error sending email: ", sys.exc_info()[0])

@app.route('/')
@basic_auth.required
def index():
    return render_template('index.html')

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(video_camera),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='PiSecurityCamera')

    parser.add_argument('-u', '--user', type=str, help='Username for flask app', default="mypiuser")
    parser.add_argument('-p', '--passwd', type=str, help='Password for flask app', default="mypicam")
    parser.add_argument('-a', '--auth', type=bool, help='Auth force', default=True)

    parser.add_argument('-e', '--email', type=str, help='Email to use as sender', default="mypiuser")
    parser.add_argument('-ep', '--emailpasswd', type=str, help='Password for Email sender', default="mypicam")
    parser.add_argument('-t', '--toemail', type=bool, help='Email destination', default=True)

    args = parser.parse_args()
    
    app.config['BASIC_AUTH_USERNAME'] = args.user
    app.config['BASIC_AUTH_PASSWORD'] = args.passwd
    app.config['BASIC_AUTH_FORCE'] = args.auth
        
    # email_sender = EmailSender(args.email, args.emailpasswd, args.toemail)
    
    t = threading.Thread(target=check_for_objects, args=())
    t.daemon = True
    t.start()

    app.run(host='0.0.0.0', debug=False)

import picamera
import numpy as np
import cv2
import sys
from flask import Flask, render_template, Response
from flask_basicauth import BasicAuth
import time
import threading
import argparse

from mail import EmailSender


# App Globals (do not edit)
email_update_interval = 300 # sends an email only once in this time interval

object_classifier = cv2.CascadeClassifier("models/fullbody_recognition_model.xml") # an opencv classifier

camera = picamera.PiCamera(resolution='720p', framerate=30) 

email_sender = None

app = Flask(__name__)
basic_auth = BasicAuth(app)

last_epoch = 0

def get_object(classifier, frame):
        found_objects = False
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        objects = classifier.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        if len(objects) > 0:
            found_objects = True

        # Draw a rectangle around the objects
        for (x, y, w, h) in objects:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        ret, jpeg = cv2.imencode('.jpg', frame)
        return (jpeg.tobytes(), found_objects)


def check_for_objects():
    global last_epoch
    global email_sender
    while True:
        try:
            img = np.empty((720 * 1280 * 3,), dtype=np.uint8)
            camera.capture(img, 'bgr')
            img = img.reshape((720, 1280, 3))
            
            frame, found_obj = get_object(object_classifier)
            if found_obj and (time.time() - last_epoch) > email_update_interval:
                last_epoch = time.time()
                print("Sending email...")
                email_sender.sendEmail(frame)
                print("done!")
        except:
            print("Error sending email: ", sys.exc_info()[0])

@app.route('/')
@basic_auth.required
def index():
    return render_template('index.html')

def gen(camera):
    while True:
        frame = np.empty((720 * 1280 * 3,), dtype=np.uint8)
        camera.capture(frame, 'bgr')
        frame = frame.reshape((720, 1280, 3))
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(camera),
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
        
    email_sender = EmailSender(args.email, args.emailpasswd, args.toemail)
    
    t = threading.Thread(target=check_for_objects, args=())
    t.daemon = True
    t.start()

    # Give the camera some warm-up time
    camera.start_preview()    
    time.sleep(2)

    app.run(host='0.0.0.0', debug=False)

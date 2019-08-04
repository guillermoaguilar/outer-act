#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
import random, math
import pyglet
from pyglet import window
from pyglet import clock
from pyglet import font
from pyglet.window import key 

## 
from picamera.array import PiRGBArray
from picamera import PiCamera
import argparse
import warnings
import datetime
import dropbox
import imutils
import json
import time
import cv2


###############################################################################
class Projection(window.Window):
    
    def __init__(self, *args, **kwargs):

        #Let all of the arguments pass through
        self.win = window.Window.__init__(self, *args, **kwargs)
        
        clock.schedule_interval(self.update, 1.0/60) # update at FPS of Hz
        
        # reading and saving images
        imsprite1 = pyglet.image.load('1.png')
        #imsprite2 = pyglet.image.load('2.png')
        #imsprite3 = pyglet.image.load('3.png')
        #imsprite4 = pyglet.image.load('4.png')
        
        self.sprite1 = pyglet.sprite.Sprite(imsprite1)
        
        # instantiating a Vision  object
        self.vision = Vision()
        
        
    def update(self, dt):
        # ask to vision object to update itself
        self.vision.update()
        

    def on_draw(self):
        self.clear() # clearing buffer
        clock.tick() # ticking the clock
            
        if self.vision.motion:
            # draw sprite
            self.sprite1.draw()
            
            
        # flipping
        self.flip()
    
    
    ## Event handlers
    def on_key_press(self, symbol, modifiers):
        
        if symbol == key.ESCAPE:
            self.dispatch_event('on_close')  
            

##################################################################    
class Vision():

    def __init__(self):
        self.conf = json.load(open('conf.json'))
        
        # set up camera and be ready to acquire
        
        # initialize the camera and grab a reference to the raw camera capture
        self.camera = PiCamera()
        self.camera.resolution = tuple(self.conf["resolution"])
        self.camera.framerate = self.conf["fps"]
        self.rawCapture = PiRGBArray(self.camera, size=tuple(self.conf["resolution"]))

        # allow the camera to warmup, then initialize the average frame, last
        # uploaded timestamp, and frame motion counter
        print("[INFO] warming up...")
        time.sleep(self.conf["camera_warmup_time"])
        self.avg = None
        self.lastUploaded = datetime.datetime.now()
        self.motionCounter = 0

        
        self.motion = False

    def update(self):
        
        # update if object has been detected or not
        
        self.camera.capture(self.rawCapture, format="bgr", use_video_port=True)
        timestamp = datetime.datetime.now()
        text = "Unoccupied"
    
        # grab the raw NumPy array representing the image and initialize
        # the timestamp and occupied/unoccupied text
        frame = self.rawCapture.array
        
        self.frame = frame
        
        # resize the frame, convert it to grayscale, and blur it
        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # if the average frame is None, initialize it
        if self.avg is None:
            print("[INFO] starting background model...")
            self.avg = gray.copy().astype("float")
            self.rawCapture.truncate(0)
            return
        
        # accumulate the weighted average between the current frame and
        # previous frames, then compute the difference between the current
        # frame and running average
        cv2.accumulateWeighted(gray, self.avg, 0.5)
        frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(self.avg))

        # threshold the delta image, dilate the thresholded image to fill
        # in holes, then find contours on thresholded image
        thresh = cv2.threshold(frameDelta, self.conf["delta_thresh"], 255,
            cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        # loop over the contours
        for c in cnts:
            # if the contour is too small, ignore it
            if cv2.contourArea(c) < self.conf["min_area"]:
                continue

            # compute the bounding box for the contour, draw it on the frame,
            # and update the text
            #(x, y, w, h) = cv2.boundingRect(c)
            #cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            text = "Occupied"
        
        # check to see if the room is occupied
        if text == "Occupied":            
            # check to see if enough time has passed between uploads
            if (timestamp - self.lastUploaded).seconds >= self.conf["min_upload_seconds"]:
                # increment the motion counter
                self.motionCounter += 1

                # check to see if the number of frames with consistent motion is
                # high enough
                if self.motionCounter >= self.conf["min_motion_frames"]:
                    # update the last uploaded timestamp and reset the motion
                    # counter
                    self.lastUploaded = timestamp
                    self.motionCounter = 0

        # otherwise, the room is not occupied
        else:
            self.motionCounter = 0
    
        # clear the stream in preparation for the next frame
        self.rawCapture.truncate(0)

        #print(text)
        if text == "Occupied":
            self.motion = True
        else:
            self.motion = False
        
###################################################################
  
if __name__ == "__main__":
    win = Projection(caption="Outer act", height=600, width=600)
    pyglet.app.run()



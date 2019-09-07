#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# TODO: 
# do it fullscreen with bigger images
# replicate behavior from scratch script: score, min time to present, and reset after no motion detected for x amount of time.
# animations x 2. 2nd happens when score > 3
# animations with ImageGrid, see performance.
# sound
#
# 
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
        
        # container for drawable objects
        self.drawableObjects = []
        self.createDrawableObjects()
        
        # reading and saving images
        #image_frames = ('1.png', '2.png', '3.png', '4.png')
        #
        #images = map(lambda img: pyglet.image.load(img), image_frames)
        #
        #animation = pyglet.image.Animation.from_image_sequence(
        #    images, 0.25)
        #
        #self.animSprite = pyglet.sprite.Sprite(animation, x=0, y=0)
        #self.animSprite.update( scale_x=1, scale_y=1)
        
        
        # instantiating a Vision  object
        self.vision = Vision()
        
        #
        self.drawing = False
        self.anim_length = 1*10 #in seconds
        
        self.motionstart = None
        self.score = 0

    def createDrawableObjects(self):
        """
        Create the objects (sprites) for drawing within the
        pyglet Window.
        """
        num_rows = 4
        num_columns = 1
        droplet = 'imgs/Sprite_01_Film_Stripe.png'
        animation = self.setup_animation(droplet,
                                         num_rows,
                                         num_columns)

        self.dropletSprite = pyglet.sprite.Sprite(animation)
        self.dropletSprite.position = (400,200)

        # Add these sprites to the list of drawables
        self.drawableObjects.append(self.dropletSprite)

    def setup_animation(self, img, num_rows, num_columns):
        """
        Create animation object using different regions of
        a single image.
        @param img: The image file path
        @type img: string
        @param num_rows: Number of rows in the image grid
        @type num_rows: int
        @param num_columns: Number of columns in the image grid
        @type num_columns: int
        """
        base_image = pyglet.image.load(img)
        animation_grid = pyglet.image.ImageGrid(base_image,
                                                num_rows,
                                                num_columns)
        image_frames = []

        for i in range(num_rows*num_columns, 0, -1):
            frame = animation_grid[i-1]
            animation_frame = pyglet.image.AnimationFrame(frame, 0.2)
            image_frames.append(animation_frame)

        animation = pyglet.image.Animation(image_frames)
        return animation
        
    def update(self, dt):

        # ask to vision object to update itself
        self.vision.update()
        
        if self.vision.motion:
                self.motionstart = time.time()
                self.score += 1
        
        currtime = time.time()
        
        if self.motionstart is not None:
                if currtime  < (self.motionstart + self.anim_length):
                        self.drawing = True
                else:
                        self.drawing = False
                        
                

    def on_draw(self):
        self.clear() # clearing buffer
        clock.tick() # ticking the clock
            
        if self.drawing:
                
            # draw sprite
            #self.animSprite.draw()
            for d in self.drawableObjects:
                d.draw()
            
            
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
    #win = Projection(caption="Outer act", width=800, height = 600)
    win = Projection(caption="Outer act", fullscreen = True)

    pyglet.app.run()



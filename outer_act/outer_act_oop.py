#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# TODO: 
# OK do it fullscreen with bigger images
# replicate behavior from scratch script: 
#   OK score, 
#   OK  min time to present, 
#   OK  and reset after no motion detected for x amount of time.
# OK animations x 2. 2nd happens when score > 3
# OK animations with ImageGrid, see performance.
# OK sound
#
# 
##

import pyglet
from pyglet import window
from pyglet import clock
from pyglet import font
from pyglet.window import key 
import time

debug = False

if debug:
    from vision_mock import Vision
else:
    from vision import Vision


###############################################################################
class Projection(window.Window):
    
    def __init__(self, *args, **kwargs):

        #Let all of the arguments pass through
        self.win = window.Window.__init__(self, *args, **kwargs)
        
        clock.schedule_interval(self.update, 1.0/60) # update at FPS of Hz
        
        # load object animations to be drawn
        self.drawableObjects = []
        self.createDrawableObjects('imgs/Sprite_01_Film_Stripe.png')
        self.createDrawableObjects('imgs/Sprite_01_2_Film_Stripe.png')
        
        self.idraw = 0
        
        # instantiating a Vision  object
        self.vision = Vision()

        # loading sounds        
        self.track =  pyglet.media.load('whatsupbro.wav', streaming=False)

        #
        self.drawing = False
        self.prev_drawing = False
        self.timelastdraw = 0
        self.maxlag = 30 # seconds
        
        self.anim_length = 1*5  # in seconds
        
        self.motionstart = None
        self.score = 0

    def createDrawableObjects(self, droplet):
        """
        Create the objects (sprites) for drawing within the
        pyglet Window.
        """
        num_rows = 4
        num_columns = 1
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
        
        currtime = time.time()
        
        if self.motionstart is not None:
            if currtime  < (self.motionstart + self.anim_length):
                self.drawing = True
            else:
                self.drawing = False
                       
            
        # update on score behavior
        if self.score < 3:
            self.idraw = 0
            
        elif self.score == 3:
            self.idraw = 1
            
        elif self.score > 3:
            # reset
            self.idraw = 0
            self.score = 0
        
        # if so much time have pass, returns score to zero
        if time.time() > (self.timelastdraw + self.maxlag):
                self.score = 0
                self.idraw = 0
                
        # creates label to show current score
        self.create_label()
        
        
        
    def create_label(self):
        
        self.label = pyglet.text.Label('Score: %d' % self.score,
              font_name='Times New Roman',
              font_size=36,
              x=100, y=100,
              anchor_x='center', anchor_y='center')
        
                    
    def on_draw(self):
        self.clear() # clearing buffer
        #clock.tick() # ticking the clock
            
        if self.drawing:
            
            # draw sprite
            self.drawableObjects[self.idraw].draw()
            
            # 
            self.label.draw()
            
            # if this is the first draw, so previouly it was false
            if not self.prev_drawing:
                self.track.play()
                self.score += 1
            
            # end of if, saves state
            self.prev_drawing = True
            self.timelastdraw = time.time()
            
        else:
            self.prev_drawing = False
            
        # flipping
        self.flip()
    
    
    ## Event handlers
    def on_key_press(self, symbol, modifiers):
        
        if symbol == key.ESCAPE:
            self.dispatch_event('on_close')  
            
        if symbol == key.M:
            self.vision.motion=True
        if symbol == key.N:
            self.vision.motion=False
            


        
###################################################################
  
if __name__ == "__main__":
    #win = Projection(caption="Outer act", width=800, height = 600)
    win = Projection(caption="Outer act", fullscreen = True)

    pyglet.app.run()



# outer-act
Test code for interactive video with camera motion detection

Fixes necessary to the actual code:

1. Start with black fullscreen:
When the code runs, the projection starts already at black fullscreen (before any motion detection)

2. Using motion speed for triggering animation:
Instead of using in line 123 "if text == "Occupied" as the trigger for the animation, I'd like to have something similar to Scratch, which is called Video Sensing. "If the video motion on Sprite > 20, then" activate animation. Basicaly that would determine a minimun motion speed to activate the animation. On line 124, the original camera surveillence code has "if motionCounter >= conf["min_motion_frames"]:", I tried to use it as a trigger, but without success. I don't know if it would work in the same way.
  
3. Sound triggered together with animation:
When the animation is triggered, the sound should be played at the same time as the first animation's frame shows up. At the present moment it is triggered before the animation.

4. Avoid latency in fullscreen and proper image resolution:
At least in my Raspberry Pi 3 B+, I had a nice smooth animation's playback when used the window in the original images' size (640 x 480). But to fulfill the fullscreen in the monitor that I'm working on right now, I increased in line 45 the image's scale "animSprite.update( scale_x=2, scale_y=2)" and had a slower playback. The goal is to create the final images at 800 x 600 pixels because that is the resolution of the mini beamer used in the box. I'd like to eliminate any possibility of latency or delayed playback. Do you think I'll have latency under these conditions?

New features to be added:

5. Create Timer and Score variables
The program needs a timer and a score variable in a game fashion way (but not displayed on screen). It is necessary to use the timer to know how long it lacks activity/ motion in the camera's view. The score counts how many times the user moved and activated the same animation loop. If the animation_1 was looped e.g. 3 times, then on the fourth time it will activate animation_2. In Scratch we have the blocks "if score > 3 then hide (Srite 1/ animation_1)" and the animation_1 is deactivated (hidden). Scratch uses a resource called "broadcast", which will activate a second parallel script in this case for the Sprite 2/ animation_2. I don't know how this could be done in Python, because in the actual code, at the window event in line 124 the animation_1 fells into a infinite loop.
  
6. Control over animation loops:
I'd like to have the possibility to control how many times the animation is looped, such as in Scratch "repeat (5)". I tried to create some "for loops" on the line 124 "@win.event", but I had no success.
  
7. Create conditions for time runned and lack of motion
If there is no movement for a certain x time since the last motion was triggered, then we go back to the initial black screen. That happens in Scratch with the block "If video motion on stage < 20 and timer > 15 then hide". And like in a game reset, the score and timer are set to zero.

8. Test motionCounter as score
About the score and timer. The actual code has a "motionCounter" variable created on line 66, which is used together in conjunction with some timestamps to define if a surveillence system has to send pictures to a dropbox. I don't know if this variable would already work as a score, maybe yes. The problem is that a score to me is a punctuation made after motion is detected and a animation loop is completed. For an example, the score should't increase while an animation cycle isn't finished. That means, a guy would shake his hand three times in front of the camera and before finishing the first loop of animation_1, the code would "jump" already to animation_2. The example in Scratch works very well, because no score is produced or a new animation is called before the first animation loop is finished.
  
9. Any key event to stop the script.

Please, if necessary check more explanations about the motion detection's code: 
 https://www.pyimagesearch.com/2015/06/01/home-surveillance-and-motion-detection-with-the-raspberry-pi-python-and-opencv/

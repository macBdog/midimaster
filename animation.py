import enum
import math

class AnimType(enum.Enum):
    FadeIn = 1
    FadeOut = 2
    Pulse = 3

class Animation:
    """ Animations store the state and timers for controller
    a variety of 2D tweens. The timer always counts down to 0.
    The value is in range 0 <= val <= 1.0 and drives the visuals.
    :param anim_type: An enum of a function describing the relation between time and val
    :param time: A float for the duration of the function
    """
    def __init__(self, anim_type: AnimType, time: float):
        self.time = time
        self.timer = time
        self.type = anim_type
        self.val = 0.0
        self.active = True
        if self.type is AnimType.FadeOut:
            self.val = 1.0
        
    def tick(self, dt: float):
        """ Update timers and values as per the animation type.
        :param dt: The time that has elapsed since the last tick.
        """
        if self.active:
            if self.type is AnimType.FadeIn:
                self.val = 1.0 - (self.timer / self.time)
            elif self.type is AnimType.FadeOut:
                self.val = self.timer / self.time
            elif self.type is AnimType.Pulse:
                self.val = math.sin(self.timer)

            self.timer -= dt
            if self.timer <= 0.0:
                self.active = False

                
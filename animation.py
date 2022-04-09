import enum
import math

class AnimType(enum.Enum):
    FadeIn = 1
    FadeOut = 2
    Pulse = 3
    InOutSmooth = 4

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
        self.action = None
        self.action_kwargs = None
        self.action_time = -1
        self.actioned = False
        if self.type is AnimType.FadeOut:
            self.val = 1.0
    
    def set_action(self, time: float, activation_func, **kwargs):
        """Setup an action to be called at a specific time in the animation.
        :param time for the time in the animation to execute, -1 means when complete.
        """
        self.action = activation_func
        if len(kwargs) > 0:
            self.action_kwargs = kwargs
        self.action_time = time

    def tick(self, dt: float):
        """Update timers and values as per the animation type.
        :param dt: The time that has elapsed since the last tick.
        """
        if self.active:
            if self.type is AnimType.FadeIn:
                self.val = 1.0 - (self.timer / self.time)
            elif self.type is AnimType.FadeOut:
                self.val = self.timer / self.time
            elif self.type is AnimType.Pulse:
                self.val = math.sin(self.timer)
            elif self.type is AnimType.InOutSmooth:
                self.val = (math.sin(((self.timer / self.time) * math.pi * 2.0) - math.pi * 0.5) + 1.0) * 0.5

            self.timer -= dt

            do_action = self.timer <= self.action_time

            if self.timer <= 0.0:
                self.active = False
                if self.action_time < 0:
                    do_action = True

            if do_action and self.action is not None:
                if not self.actioned:
                    if self.action_kwargs is None:
                        self.action()
                    else:
                        self.action(self.action_kwargs)
                    self.actioned = True

                
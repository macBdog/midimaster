import functools
import time

class Profile:
    Frames = {}
    Capture = False
    CaptureFrame = 0
    QueuedFrame = 0
    CurFrameName = None
    CurFrameTime = 0
    
    @staticmethod
    def capture_next_frame():
        Profile.QueuedFrame += 1

    @staticmethod
    def dump():
        print("QnD Profile Report:")
        for _, frame in enumerate(Profile.Frames):
            print(f'{frame}: {Profile.Frames[frame] * 1000}')

    @staticmethod
    def update():    
        if Profile.QueuedFrame > Profile.CaptureFrame:
            if Profile.Capture:
                Profile.CaptureFrame += 1
                Profile.Capture = False
                Profile.dump()
            else:
                Profile.Frames = {}
                Profile.Capture = True

    @staticmethod
    def begin(name: str):
        Profile.CurFrameName = name
        Profile.CurFrameTime = time.perf_counter()

    @staticmethod
    def end():
        Profile.add_frame(Profile.CurFrameName, Profile.CurFrameTime, time.perf_counter())

    @staticmethod
    def add_frame(name: str, start_time: float, end_time: float):
        if Profile.Capture:
            Profile.Frames[name] = end_time - start_time
        
def profile(func):
    """Store the runtime of a decorated function"""
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        Profile.add_frame(start_time, end_time, func.__name__)
        return value
    return wrapper_timer

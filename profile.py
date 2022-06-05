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
        title = "Profile Total"
        pad = len(title) + 12
        total_time_s = 0.0
        fill = '█'
        for name in Profile.Frames:
            total_time_s += float(Profile.Frames[name])
        bar = fill * 100
        total_time_ms = total_time_s * 1000.0
        trace = f"100% - {round(total_time_ms, 3)}ms {round(1.0 / total_time_s, 1)}fps"
        print(f"{title.ljust(pad)}: {trace.ljust(pad)} {bar}")
        for name in Profile.Frames:
            time_ms = Profile.Frames[name] * 1000
            pct = (time_ms / total_time_ms) * 100
            trace = f"{round(pct, 0)}% - {round(time_ms, 3)}ms"
            bar = fill * int(pct)
            print(f"{name.ljust(pad)}: {trace.ljust(pad)} {bar}")

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

import time
import threading

def RunEvery(Duration, Function, *args, **kwargs):
    def Wrapper():
        while True:
            Start = time.time()
            Function(*args, **kwargs)
            time.sleep(Duration - (time.time() - Start))
    threading.Thread(target=Wrapper, daemon=True).start()

def RunIn(Duration, Function, MainThread=False, *args, **kwargs):
    if not MainThread:
        def Wrapper():
            time.sleep(Duration)
            Function(*args, **kwargs)
        threading.Thread(target=Wrapper, daemon=True).start()
    else:
        def Wrapper():
            time.sleep(Duration)
            Function(*args, **kwargs)
        threading.Timer(Duration, Wrapper).start()

def RunInMainThread(Function, *args, **kwargs):
    RunIn(0, Function, MainThread=True, *args, **kwargs)
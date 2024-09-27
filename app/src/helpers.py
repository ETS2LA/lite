import time
import threading

def RunEvery(duration, function, *args, **kwargs):
    def wrapper():
        while True:
            start = time.time()
            function(*args, **kwargs)
            time.sleep(duration - (time.time() - start))

    thread = threading.Thread(target=wrapper, daemon=True)
    thread.daemon = True
    thread.start()

def RunIn(duration, function, mainThread=False, *args, **kwargs):
    if not mainThread:
        def wrapper():
            time.sleep(duration)
            function(*args, **kwargs)

        thread = threading.Thread(target=wrapper, daemon=True)
        thread.daemon = True
        thread.start()
    else:
        def wrapper():
            time.sleep(duration)
            function(*args, **kwargs)

        threading.Timer(duration, wrapper).start()

def RunInMainThread(function, *args, **kwargs):
    RunIn(0, function, mainThread=True, *args, **kwargs)
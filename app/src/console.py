import src.variables as variables
import src.plugins as plugins
import multiprocessing
import win32console
import win32con
import win32gui
import traceback
import ctypes
import time


RED = "\033[91m"
NORMAL = "\033[0m"


def RestoreConsole():
    try:
        if variables.ConsoleHWND != None and variables.ConsoleName != None:
            win32gui.ShowWindow(variables.ConsoleHWND, win32con.SW_RESTORE)
        else:
            variables.ConsoleName = win32console.GetConsoleTitle()
            variables.ConsoleHWND = win32gui.FindWindow(None, str(variables.ConsoleName))
            win32gui.ShowWindow(variables.ConsoleHWND, win32con.SW_RESTORE)
    except:
        Type = "\nConsole - Restore Error."
        Message = str(traceback.format_exc())
        while Message.endswith('\n'):
            Message = Message[:-1]
        if variables.DevelopmentMode == False:
            Message = f"{RED}>{NORMAL} " + Message.replace("\n", f"\n{RED}>{NORMAL} ")
        print(f"{RED}{Type}{NORMAL}\n{Message}\n")
        ProcessName = multiprocessing.current_process().name
        if ProcessName != "MainProcess":
            while True:
                variables.QUEUE = []
                plugins.AddToQueue({"POPUP": [f"{ProcessName} Crashed!", 0, 0.5]})
                plugins.AddToQueue({"MANAGEPLUGINS": [str(ProcessName), "Stop"]})
                DATA = variables.QUEUE
                DataBytes = plugins.pickle.dumps(DATA)
                plugins.SHARED_MEMORY.buf[:variables.SHARED_MEMORY_SIZE][:len(DataBytes)] = DataBytes
                time.sleep(0.1)


def HideConsole():
    try:
        if variables.ConsoleHWND != None and variables.ConsoleName != None:
            win32gui.ShowWindow(variables.ConsoleHWND, win32con.SW_HIDE)
        else:
            variables.ConsoleName = win32console.GetConsoleTitle()
            variables.ConsoleHWND = win32gui.FindWindow(None, str(variables.ConsoleName))
            win32gui.ShowWindow(variables.ConsoleHWND, win32con.SW_HIDE)
    except:
        Type = "\nConsole - Hide Error."
        Message = str(traceback.format_exc())
        while Message.endswith('\n'):
            Message = Message[:-1]
        if variables.DevelopmentMode == False:
            Message = f"{RED}>{NORMAL} " + Message.replace("\n", f"\n{RED}>{NORMAL} ")
        print(f"{RED}{Type}{NORMAL}\n{Message}\n")
        ProcessName = multiprocessing.current_process().name
        if ProcessName != "MainProcess":
            while True:
                variables.Queue = []
                plugins.AddToQueue({"POPUP": [f"{ProcessName} Crashed!", 0, 0.5]})
                plugins.AddToQueue({"MANAGEPLUGINS": [str(ProcessName), "Stop"]})
                DATA = variables.Queue
                DataBytes = plugins.pickle.dumps(DATA)
                plugins.SHARED_MEMORY.buf[:variables.SharedMemorySize][:len(DataBytes)] = DataBytes
                time.sleep(0.1)

def CloseConsole():
    try:
        if variables.ConsoleName != None and variables.ConsoleName != None:
            ctypes.windll.user32.PostMessageW(variables.ConsoleHWND, 0x10, 0, 0)
        else:
            variables.ConsoleName = win32console.GetConsoleTitle()
            variables.ConsoleHWND = win32gui.FindWindow(None, str(variables.ConsoleName))
            ctypes.windll.user32.PostMessageW(variables.ConsoleHWND, 0x10, 0, 0)
    except:
        Type = "\nConsole - Close Error."
        Message = str(traceback.format_exc())
        while Message.endswith('\n'):
            Message = Message[:-1]
        if variables.DevelopmentMode == False:
            Message = f"{RED}>{NORMAL} " + Message.replace("\n", f"\n{RED}>{NORMAL} ")
        print(f"{RED}{Type}{NORMAL}\n{Message}\n")
        ProcessName = multiprocessing.current_process().name
        if ProcessName != "MainProcess":
            while True:
                variables.Queue = []
                plugins.AddToQueue({"POPUP": [f"{ProcessName} Crashed!", 0, 0.5]})
                plugins.AddToQueue({"MANAGEPLUGINS": [str(ProcessName), "Stop"]})
                DATA = variables.Queue
                DataBytes = plugins.pickle.dumps(DATA)
                plugins.SHARED_MEMORY.buf[:variables.SharedMemorySize][:len(DataBytes)] = DataBytes
                time.sleep(0.1)
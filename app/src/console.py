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
        if variables.CONSOLEHWND != None and variables.CONSOLENAME != None:
            win32gui.ShowWindow(variables.CONSOLEHWND, win32con.SW_RESTORE)
        else:
            variables.CONSOLENAME = win32console.GetConsoleTitle()
            variables.CONSOLEHWND = win32gui.FindWindow(None, str(variables.CONSOLENAME))
            win32gui.ShowWindow(variables.CONSOLEHWND, win32con.SW_RESTORE)
    except:
        Type = "\nConsole - Restore Error."
        Message = str(traceback.format_exc())
        while Message.endswith('\n'):
            Message = Message[:-1]
        if variables.DEVMODE == False:
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
        if variables.CONSOLEHWND != None and variables.CONSOLENAME != None:
            win32gui.ShowWindow(variables.CONSOLEHWND, win32con.SW_HIDE)
        else:
            variables.CONSOLENAME = win32console.GetConsoleTitle()
            variables.CONSOLEHWND = win32gui.FindWindow(None, str(variables.CONSOLENAME))
            win32gui.ShowWindow(variables.CONSOLEHWND, win32con.SW_HIDE)
    except:
        Type = "\nConsole - Hide Error."
        Message = str(traceback.format_exc())
        while Message.endswith('\n'):
            Message = Message[:-1]
        if variables.DEVMODE == False:
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

def CloseConsole():
    try:
        if variables.CONSOLEHWND != None and variables.CONSOLENAME != None:
            ctypes.windll.user32.PostMessageW(variables.CONSOLEHWND, 0x10, 0, 0)
        else:
            variables.CONSOLENAME = win32console.GetConsoleTitle()
            variables.CONSOLEHWND = win32gui.FindWindow(None, str(variables.CONSOLENAME))
            ctypes.windll.user32.PostMessageW(variables.CONSOLEHWND, 0x10, 0, 0)
    except:
        Type = "\nConsole - Close Error."
        Message = str(traceback.format_exc())
        while Message.endswith('\n'):
            Message = Message[:-1]
        if variables.DEVMODE == False:
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
import src.variables as variables
import json
import time
import os


def Lock():
    try:
        Count = 0
        while os.path.exists(f"{variables.Path}config/settings-lock.txt"):
            time.sleep(0.001)
            Count += 1
            if Count > 100:
                break
        with open(f"{variables.Path}config/settings-lock.txt", "w") as File:
            File.write("")
        File.close()
    except:
        pass


def Free():
    try:
        if os.path.exists(f"{variables.Path}config/settings-lock.txt"):
            os.remove(f"{variables.Path}config/settings-lock.txt")
    except:
        pass


def EnsureFile(FileStr:str):
    try:
        if os.path.exists(FileStr) == False:
            with open(FileStr,  "w"):
                File.write("{}")
        with open(FileStr, "r") as File:
            try:
                json.load(File)
            except:
                with open(FileStr, "w") as FileFile:
                    FileFile.write("{}")
    except:
        with open(File, "w") as File:
            File.write("{}")


def Get(Category:str, Name:str, Value:any=None):
    try:
        Lock()
        EnsureFile(f"{variables.Path}config/settings.json")
        with open(f"{variables.Path}config/settings.json", "r") as File:
            Settings = json.load(File)
        File.close()
        Free()

        if Settings[Category][Name] == None:
            return Value

        return Settings[Category][Name]
    except:
        Free()
        if Value != None:
            Set(Category, Name, Value)
            return Value
        else:
            pass


def Set(Category:str, Name:str, Data:any):
    try:
        Lock()
        EnsureFile(f"{variables.Path}config/settings.json")
        with open(f"{variables.Path}config/settings.json", "r") as File:
            Settings = json.load(File)
        File.close()

        if not Category in Settings:
            Settings[Category] = {}
            Settings[Category][Name] = Data

        if Category in Settings:
            Settings[Category][Name] = Data

        with open(f"{variables.Path}config/settings.json", "w") as File:
            File.truncate(0)
            json.dump(Settings, File, indent=6)
        File.close()
        Free()
    except:
        Free()
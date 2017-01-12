import time


def runFile(comp, file):
    """Given WMI Object comp, formatted file, run file on WMI client. Returns pid of last command ran"""
    startDir = "C:\\"
    stop = False
    pid = None
    with open(file, 'r') as contents:
        for line in contents:
            handles = {
                '#': 'skip',
                '*': 'dontWait',
                '~': 'start',
                '&': 'queryStart',
                '$': 'queryEnd'
            }
            handle = ""
            for key, value in handles.items():
                if line[0] is key:
                    handle = value
                    line = line[1:]
                    break

            print(line)
            if handle is "start":
                startDir = line
            elif handle is "queryStart":
                if not comp.query(line):
                    stop = True
            elif handle is "queryEnd":
                if stop:
                    stop = False
                else:
                    raise IndexError("Asked query to end before it began")
            elif handle is "skip" or stop or not line:
                pass
            else:
                print("Running:", line, "on", comp)
                pid, statCode = comp.Win32_Process.Create(CommandLine=line, CurrentDirectory=startDir)
                if statCode == 0:
                    pass
                else:
                    raise RuntimeError("Error running command: " + line)
                if handle is not "dontWait":
                    while True:
                        if comp.Win32_Process(ProcessId=pid):
                            time.sleep(0.5)
                        else:
                            break
        return pid

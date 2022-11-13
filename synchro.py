# IMPORTS (all default libraries)
from os import listdir, mkdir, remove, path
import time
from datetime import datetime, date
import shutil
from filecmp import cmp
from math import ceil

# GLOBAL VARIABLES
DEFAULT_INTERVAL = 0.25     # if ongoing mode: backup cycle occurs every 1/2 hour by default
TIME_QUANTUM = 3600         # time quantum for ongoing mode
# MAXIMUM_CYCLES = 100      # if ongoing mode: API ends after 100 backup cycles by default

class Synchro():
    def __init__(self):
        self.logfile = None     # the current log file
        self.source = None
        self.replica = None
        self.mode = None        # the API usage mode (ongoing or singular)
        self.proper = True      # boolean to track if api will work (to avoid throwing excessive errors)
        self.interval = None
        self.max = -1
        self.interrupted = False  # to keep track of interrupt has occurred

    def update_log(self):
        '''
        If the date has changed, closes the current log file, then creates a new one with today's date.
        '''
        if not path.exists("./LOGS/LOG-" + str(date.today()) + ".txt"):
            self.logfile.close()
            self.logfile = open("./LOGS/LOG-" + str(date.today()) + ".txt", "a")

    def open_log(self):
        ''''
        Creates a logs directory if it doesn't exist. Creates/opens the log file corresponding to today's date.
        '''
        if not path.exists("./LOGS"):
            mkdir("LOGS")

        self.logfile = open("./LOGS/LOG-" + str(date.today()) + ".txt", "a")
    
    def configure(self, source, replica, mode="s", interval=DEFAULT_INTERVAL, max=-1):
        '''
        Sets the logfile. Configures the API object with all its attributes.
        '''
        if self.interrupted:
            print("The API was previously interrupted and the API was forced to shutdown early. close_api() method failed.")
            return None

        # self.logfile = open(f"./LOGS/LOG-{str(date.today()).txt}", "a")
        self.open_log()
        
        if not path.isdir(source):
            print(f"Error: {source} is not a directory. Configuration failed")
            self.logfile.write("-"*128+"\n")
            self.logfile.write(f"Error: {source} is not a directory. Configuration failed\n")
            self.proper = False
        if not path.isdir(replica):
            print(f"Error: {replica} is not a directory. Configuration failed")
            self.logfile.write("-"*128+"\n")
            self.logfile.write(f"Error: {replica} is not a directory. Configuration failed\n")
            self.proper = False
        if replica=="LOGS" or replica=="./LOGS":
            print(f"Error: LOGS cannot be the replica directory. Configuration failed")
            self.logfile.write("-"*128+"\n")
            self.logfile.write(f"Error: LOGS cannot be the replica. Configuration failed\n")
            self.proper = False
        
        if self.proper:
            if mode.lower()=="o":
                if type(interval) is int or type(interval) is float:
                    if interval<DEFAULT_INTERVAL:
                        self.interval = DEFAULT_INTERVAL
                        print("Interval provided is too short. A default value will be used instead")
                    elif interval>24:
                        self.interval = 24
                        print("Interval provided is too long. This API supports synchronization at frequency of minimum 1 time" 
                            "per day.")
                    else:
                        self.interval = interval
                    print(f"Parameters for ongoing mode: scheduling interval set to {self.interval}")
                else:
                    print("Error in ongoing mode interval: invalid argument for time interval. The interval will be set to a "
                        "default value.")
                    self.interval = 1
                
                if max>0:
                    if max<1000:
                        self.max = ceil(max)
                    else:
                        self.max = 999
                        print("The maximum cycles parameter provided is too high, the maximum number of cycles set to 999.")

            self.source = source
            self.replica = replica
            if mode.lower()=="o":
                self.mode = "ongoing"
                print("In ongoing mode (script mode)")
            elif mode.lower() == "s":
                self.mode = "single"
                print("In single mode (task scheduler mode)")
            else:
                self.mode = "single"
                print(f"Mode {mode} not recognized. Synchronization mode set to single (task scheduler mode) by default")
        
    # close existing file and create a new one if the day has changed; run this in the while loop
    
    def traverse(self, s, r, flag=False):
        '''
        Traverses the source & replica directories and conducts backup.
        Function is recursive to hit all subdirectories.
        '''
        if flag:
            self.logfile.write("-"*128+"\n")
            self.logfile.write(f"***SYNCHRONIZATION API RUNNING IN {self.mode.upper()} MODE***\n")

        list_s = listdir(s)
        list_r = listdir(r)

        # dictionary to represent the files to be created, overwritten, and deleted
        files = {
            "create": [],
            "overwrite": [],
            "delete": []
        }
        dirs = {
            "create": [],
            "overwrite": [],
            "delete": []
        }

        # Files that exist in the source will be written/overwritten into replica
        for entry in list_s:
            dir = path.isdir(s + "/" + entry)
            if entry not in list_r:
                flag = "create"
            else:
                flag = "overwrite"
            
            if dir:
                dirs[flag].append(entry)
            else:
                files[flag].append(entry)

        # Files that exist in replica but not in source will be deleted
        for entry in list_r:
            dir = path.isdir(r + "/" + entry)
            if entry not in list_s:
                if dir:
                    # since will just be removing these, we can reference the absolute path
                    dirs["delete"].append(r + "/" + entry) 
                else:
                    files["delete"].append(r + "/" + entry)

        # copy, overwrite, or delete files
        for c in files["create"]:
            try:
                shutil.copy(s+"/"+c, r)
                x = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + f"--Created file {c} into folder {r}\n")
                print(f"Created file {c} into folder {r}")
            except PermissionError:
                print("Error: permission denied on " + c)
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + f"--Error: permission denied on {c} when "
                "trying to copy file from {s} to {r}\n")

        for c in files["overwrite"]:
            # first check if the files are different
            if cmp(s+"/"+c, r+"/"+c):
                print(f"The file {c} is the same, it will not be replaced")
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + f"--Overwrite of {c} in folder {r} did NOT "
                "occur, since it is up to date\n")
                continue

            # next check if file is opened, continue if it is
            try:
                remove(f"{r}/{c}")
            except OSError:
                print(f"OS Error occurred when trying to overwrite {c} in directory {r}")
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+f"--OS Error occurred when trying to overwrite"
                " {c} in directory {r}\n")
                continue

            # overwrite process is a file remove, then copy
            try:
                shutil.copy(s + "/" + c, r)
                print(f"Overwrote {c} in folder {r}")
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + f"--Overwrote {c} in folder {r}\n")
            except PermissionError:
                print(f"Permission denied when copying {c} into the target folder")
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S") + f"--Error: permission denied on {c} when "
                "trying to copy file from {s} to {r} during overwrite\n")

        for c in files["delete"]:
            try:
                remove(c)
                print(f"Removed file {c}")
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+f"--Removed file {c}\n")
            except OSError as error:
                print(f"OS Error occurred when trying to remove {c} in directory {r}")
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+f"--OS Error occurred when trying to remove "
                "{c} in directory {r}: {error}\n")

        # copy or delete folders
        for d in dirs["create"]:
            # these are the directories to copy completely
            try:
                shutil.copytree(s+"./"+d, r+"./"+d)
                print(f"Copied the tree {d} into folder {r}")
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+f"--Copied the tree {d} into folder {r}\n")
            except PermissionError:
                print(f"PermissionError occurred when trying to copy the tree {d} into folder {r}")
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+f"--PermissionError occurred when trying to "
                "copy the tree {d} into folder {r}\n")

        for d in dirs["delete"]:
            try:
                shutil.rmtree(d)
                print(f"Removed directory {d}")
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+f"--Removed directory {d}\n")
            except PermissionError as error:
                print(f"OS Error occurred when trying to remove directory {d}")
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+f"--OS Error occurred when trying to remove "
                "directory {d}: {error}\n")

        # if source and replica have matching subdirectories, traverse them iteratively
        for d in dirs["overwrite"]:
            self.traverse(f"{s}/{d}", f"{r}/{d}")

    def close_api(self, interrupt=False):
        '''
        Closes the logfile. More functionality may be implemented later.
        '''
        if self.interrupted:
            print("The API was previously interrupted and the API was forced to shutdown early. close_api() method failed.")
        elif self.proper:
            if interrupt:
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+f"--THE SYNCHRONIZATION API HAS TERMINATED "
                    "EARLY DUE TO KEYBOARD INTERRUPT\n")
                print("The synchronization API has terminated early due to keyboard interrupt")
            else:
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+f"--THE SYNCHRONIZATION API HAS TERMINATED "
                    "ORGANICALLY\n")
                print("The synchronization API has terminated")

            self.logfile.close()
        else:
            print("The API was misconfigured, there was nothing to close.")
    
    def run(self):
        '''
        Runs the API. Single mode: a single backup cycle occurs. Ongoing mode: a while loop occurs.
        '''
        if self.interrupted:
            print("The API was previously interrupted and the API was forced to shutdown early. close_api() method failed.")
            return None

        if self.proper:
            self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+f"--Synchronization started on folders "
                "{self.source} (source), {self.replica} (replica).\n")
            if self.mode=="single":
                print("Synchronization will run in single mode (one synchronization will happen, then API will terminate).")
                self.traverse(self.source, self.replica, True)
                self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"--Synchronization completed.\n")
                # self.close_api()
                # opening and closing log file so that the user can see the logs dynamically
            else:
                if self.max==-1:
                    print(f"Synchronization will run in ongoing mode, synchronization will occur once every {self.interval}"
                        " hour(s). No maximum specified on number of backup cycles, the API will run indefinitely.")
                else:
                    print(f"Synchronization will run in ongoing mode, synchronization will occur once every {self.interval}" 
                        f" hour(s) for a maximum of {self.max} backup cycles.")
                print("The API can be terminated at any time by pressing CTRL+C")
                count = 0
                while True:
                    try:
                        self.traverse(self.source, self.replica, True)
                        print("Synchronization occurred. The API can be terminated at any moment by pressing CTRL+C on the"
                            "keyboard")
                        self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"--Synchronization completed.\n")
                        self.logfile.close()
                        self.open_log()
                        count+=1
                        if count==self.max:
                            break
                        time.sleep(self.interval * TIME_QUANTUM)
                    except KeyboardInterrupt:
                        print("The loop will now terminate")
                        self.close_api(interrupt=True)
                        self.interrupted = True
                        break
                if self.max != -1:
                    print(f"A total of {count} backup cycles were performed")
        else:
            self.logfile.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+f"--Tried to run the API, failed because it wasn't"
                "configured properly. See logs for details.\n")
            print("Tried to run the API, failed because it wasn't configured properly. See logs for details.")
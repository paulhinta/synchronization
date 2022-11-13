# synchronization
Synchronization API to manage backups between two folders

## Description
This API is developed to service the backup between two folders, _source_ and _replica_. This API supports two modes: _ongoing_ and _single_; usage depends on the user's preference. The user is able to call the API from the command line or by including it in a Python script.

The ongoing mode will run a loop that will either run indefinitely or until a certain limit (which can be specified by the user) is reached. This may be preferred if the user wants to monitor and backup only one folder over time and has the capacity to run this script in the background of their computer. The _ongoing_ mode can be interrupted at any time via keyboard interrupt (CTRL+C), which is handled and logged by the API.

The single mode will run one backup cycle at a time, which is more useful if the user prefers to schedule the backup of multiple folders at once. For instance, if the user wants to schedule the backup of three folders every 24h, they would require three different instances of an API running in ongoing mode. However, with single mode, the user can write a script to backup each folder once, and then schedule this script to run every 24h using a tool such as Windows Task Scheduler or MacOS crontab.

## Usage

### Command Line

To run the API in the command line, four keyword arguments are required:

__source__: A _String_ containing the path to the source folder. Relative or absolute path is accepted.

__replica__: A _String_ containing the path to the destination folder. Relative or absolute path is accepted.

__interval__: An _int_ or _float_ representing how many hours the API will wait until the next backup cycle.

__logpath__: A _String_ containing the path to the _LOGS_ folder. If _LOGS_ does not exist in this location, it will be created as a subdirectory.

Usage:

```
python synchro.py -<source> -<replica> -<interval> -<logpath>
```
If running the API in the command line, the operation mode is automatically set to indefinite ongoing (a backup cycle will occur every <interval> hour(s) until the user stops it with CTRL+C).

### Python Scripting

Like other APIs in Python, the synchronization API is a class, making it very versatile and usable in Python scripts.

#### Instantiation

To use the API inside a script, it must first be instantiated. For instance:
```python
from synchro import Synchro

s = Synchro()
```
Instantiation takes one optional argument:

__logpath__: A _String_ containing the path to the _LOGS_ folder. If _LOGS_ does not exist in this location, it will be created as a subdirectory. If this argument is not specified, the _LOGS_ folder will be created in the current working directory.

#### Configuration

Note that upon instantiation, only the path to the logs are attributed. The other attributes must be assigned by calling the method _configure()_, which takes the following parameters:

__source__: A String containing the path to the source folder. Relative or absolute path is accepted.

__replica__: A String containing the path to the destination folder. Relative or absolute path is accepted.

Configuration will fail if either folder does not exist or if the _LOGS_ subfolder is selected as the replica directory.

#### Executing a backup

The _run()_ method is used to conduct the backup. The _close_api()_ method should be called at the end of the script, otherwise the data in the backup log may not be up to date.

```python
from synchro import Synchro

s = Synchro()
s.configure("source", "folder")
s.run()
s.close_api()
```

Additionally, configure accepts the following optional arguments:
    

__mode__: A _String_, "s" or "S" to represent single mode, "o" or "O" to represent ongoing mode. If a String other than these is passed, the API will automatically be set to _single_ mode.


__interval__: An _int_ representing the period (in hours) at which the backup cycles should occur in _ongoing_ mode. If this value is below 0.25, it is set to this upper limit (a lower bound is necessary to make sure that each backup cycle has enough time to run to completion in case the user is backing up a large directory). This parameter affects only _ongoing_ mode.

__max__: An _int_ representing the maximum number of iterations (backup cycles) to run before the loop is broken. If this number is not specified, it will run indefinitely. If a float is passed, the API will take the ceiling. If a negative number or non-int/non-float is passed, the API will run indefinitely by default.


The _configure()_ method is useful particularly useful for reconfiguring the Synchro object based on the user's needs. This allows the user to run one script to backup multiple folders. For instance:

```python
from synchro import Synchro

s = Synchro()
s.configure("source1", "folder1")
s.run()
s.configure("source2", "folder2")
s.run()
s.configure("source2", "folder3")       # in one script execution, two folders are backed up to three locations
s.run()
s.close_api()
```

Below is an example of how to use the API in ongoing mode:
```python
from synchro import Synchro

s = Synchro()
s.configure("source1", "folder1", "O", interval=4)    # The API will run a backup cycle every 4 hours, indefinitely
s.run()
s.close_api()
```

### How a backup works
The API uses PyPi libraries to execute the backup. In comparing the two folders, it will decide which files & folders to copy from _source_ to _replica_, which ones to delete from _replica_, and which ones to overwrite (i.e. ones that have the same name). Overwritting is handled differently for files and folders. For a file that needs to be overwritten, the file will first be deleted in _replica_, then copied from _source_. For a folder that needs to be overwritten, the API will compare the contents of the folders and make decisions from there. This means that the backup process is recursive, so each subdirectory is handled.

## Backup logging
If configuration is successful, the API will search for a folder called _LOGS_ in the _logpath_ specified by the user. If this folder does not exist, it will be generated. Next, it will create a textfile as the logfile and place it inside this folder; the log file's name has format _LOG-YYYY-MM-DD.txt_. Each time _run()_ is called, the API will check if the log file name should be updated (in case the date has changed); in this case, the API will close the file and generate a new one automatically. The _LOGS_ file is generated automatically in the same folder that the script is run in (not where the API resides). This means that in a script, say _test.py_, a user can call _sys_ to add the path to _synchro.py_ to the site packages and the _LOGS_ folder will be generated in the same directory as _test.py_.

```
C:.
│   synchro.py
│
└───my_folder
    │   test.py
    │
    └───LOGS
            LOG-2022-11-12.txt
```

Each time a backup occurs, the API will log a message containing a timestamp and information on which file(s) and folders were added, deleted, or overwritten, as well as those that remained untouched. Logging will also occur on certain user errors. These messages are appended onto the current working log file.

## Known Issues
This section describes some issues that I encountered while developing this API. I would love any feedback on this!
    
### Mutual Exclusion
Currently, this API does not support mutual exclusion. This means that a file can be overwritten or deleted while it is opened by another process. Ideally, if a file is opened in another process while the API tries to modify it, it would be skipped over during this backup cycle. This is a corner case that should always be addressed, but it likely does not affect the function of the API (if a user is running a cyclical, scheduled backup on _source_ into _replica_, they know that the data in the _replica_ folder will be synced up to the most up-to-date version of _source_, therefore there
s no reason to be modifying the data in the _replica_ directory). 

Here is an example of my latest attempt at mutual exclusion (which did not work because it ended up skipping over all the files). It was implemented in the _for_ loops of the _traverse()_ function:
```python
# IMPORTS
from os import rename
'''
'''

class Synchro():
    '''
    '''
    def traverse(self, s, r, flag=False):
        '''
        '''
        for c in files["overwrite"]:
            try:
                rename(c, c)
            except OSError:
                print(f"The file {c} is opened by another process. It will not be backed up during this cycle")
                continue
        '''
        '''
```
I made another attempt by trying to check the current file path against all the open files using _proc.open_files()_, but this method was inconsistent.

The mutual exclusion problem also introduces issues in running multiple synchronization APIs in the same location. For instance, if two scripts exist in the same folder and each is calling the synchronization API, they will be competing with each other for the log file (since both of them will be looking for the file with today's date in the _LOGS_ subfolder). 

Perhaps C would have been a better language to tackle this problem in, since mutex implementation with the _pthreads_ library is robust and very simple to implement. 

### Hidden Files
In traversing the _source_ and _replica_ directories, the API calls _shutil_ to modify the directory structure. There appears to be some issues with calling _shutil_ on hidden files or directories, particularly when copying a folder (i.e. when calling _shutil.copytree()_).

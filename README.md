# synchronization
Synchronization API to manage backups between two folders

## Description
This API is developed to service the backup between two folders, _source_ and _replica_. This API supports two modes: _single_ and _ongoing_; usage depends on the user's preference.

The single mode will run one backup cycle at a time, which is more useful if the user prefers to schedule the backup of multiple at once. For instance, the user can write a script containing the backup of three different directories in single mode and schedule them using an external tool such as the Windows Task Scheduler or MacOS crontab.

The ongoing mode will run a loop that will either run indefinitely or until a certain limit (which can be specified by the user) is reached. This may be preferred if the user wants to monitor and backup only one folder over time and has the capacity to run this script in the background of their computer. The _ongoing_ mode can be interrupted at any time via keyboard interrupt (CTRL+C), which is handled and logged by the API.

## Usage

### Instantiation

Like other APIs in Python, the synchronization API is a class. To use it, it must first be instantiated. For instance:
```python
from synchro import Synchro

s = synchro()
```

### Configuration

Note that upon instantiation, the object's attributed are not assigned. This must be done by calling the method _configure()_, which takes the following parameters:

__source__: A String containing the path to the source folder. Relative or absolute path is accepted.

__replica__: A String containing the path to the destination folder. Relative or absolute path is accepted.

Configuration will fail if either folder doesn't exist.

### Executing a backup

The _run()_ method is used to conduct the backup. The _close_api()_ method should be called at the end of the script, otherwise the data in the backup log may not be up to date.

```python
from synchro import Synchro

s = Synchro()
s.configure("source", "folder")
s.run()
s.close_api()
```

Additionally, configure accepts the following optional arguments:


__mode__: A String, "s" or "S" to represent single mode, "o" or "O" to represent ongoing mode. If a String other than these is passed, the API will automatically be set to _single_ mode.


__interval__: An int representing the period (in hours) at which the backup cycles should occur in _ongoing_ mode. If this value is below 0.25 or above 24, it is set to these limits (this is just to make development easier, realistically only a lower bound is necessary to make sure that each backup cycle has enough time to run to completion). This parameter affects only _ongoing_ mode.


__max__: An int representing the maximum number of iterations (backup cycles) to run before the loop is broken. If this number is not specified, it will run indefinitely. If a float is passed, the API will take the ceiling. If a negative number or non-int/non-float is passed, the API will run indefinitely by default.



The configuration is useful particularly in single mode. This allows the user to run one script to backup multiple folders. For instance:

```python
from synchro import Synchro

s = Synchro()
s.configure("source1", "folder1")
s.run()
s.configure("source2", "folder2")
s.run()
s.configure("source3", "folder3")
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
If configuration is successful, the API will search for a folder called _LOGS_. If this folder doesn't exist, it will be generated. Next, it will create a textfile as the logfile and place it inside this folder; the log file's name has format _LOG-YYYY-MM-DD.txt_. Each time _run()_ is called, the API will check if the log file name should be updated (in case the date has changed). In such a case, the API will close the file and generate a new one automatically.


Each time a backup occurs, the API will log a message informing the user of which file(s) and folders were added, deleted, or overwritten, as well as those that remained untouched. Certain errors are also logged onto the logfile and the console (terminal). The log file contains the exact timestamp at which the backup occurs; the console contains only the messages.

## Known Issues
Currently, this API does not support mutual exclusion. This means that a file can be overwritten or deleted while it is opened by another process. Ideally, if a file is opened in another process while the API tries to modify it, it would be skipped over during this backup cycle, but I wasn't able to implement it yet. I'd love any feedback on this!

Here is an example of my latest attempt at mutual exclusion (which didn't work because it ended up skipping over all the files). It was implemented in the _for_ loops of the _traverse()_ function:
```python
# IMPORTS
from os import rename
'''
...
'''

def traverse(self, s, r, flag=False):
    '''
    ...
    '''
    for c in files["overwrite"]:
        try:
            rename(c, c)
        except OSError:
            print(f"The file {c} is opened by another process. It will not be backed up during this cycle")
            continue
    '''
    ...
    '''
```

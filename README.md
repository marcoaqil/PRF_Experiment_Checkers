# PRF_Experiment
Repository for PRF mapping experiment stimulus

Requirements: psychopy and exptools2

**Usage**

Create setting files named expsettings_*Task*.yml within the Experiment folder. Change *Task* to your actual task name. Run the following line from within the Experient folder. This particular version also compatibility with the eyetracker and subject-specific delimitation of the visual field from within the scanner. Therefore, we have two extra flags that must be used together. 

```python
python main.py sub-*xxx* ses-*x* task-*NameTask* run-*x* *eyetracker [0=**no**|1=**yes**]* *delimiter [0=**no**|1=**yes**]*
```

Subject SHOULD be specified according the the BIDS convention (sub-001, sub-002 and so on), Task MUST match one of the settings files in the Experiment folder, and Run/eyetracker/delimiter SHOULD be an integers.

For example:
```python
            #  sub  ses task    # run   # eye   # delim
python main.py 999  1   "2R"    1       1       1
python main.py 999  1   "2R"    1       1       0
```

**Marco's PRF mapping**

The Experiment folder contains 5 setting files, which can be used as examples. The Task names are:

- 2R: 2 squares, Regular speed (20TR bar passes, aka 30 seconds with our standard sequence)
- 4R: 4 squares, Regular speed 
- 1R: 1 square, Regular speed
- 4F: 4 squares, Fast speed (10TR bar passes, double the normal speed)
- 1S: 1 square, Slow speed (40TR bar passes, half the normal speed)

Note that the actual task (fixation dot color discrimination) is identical in all 5 cases.

**Settings file** 

In the settings file you should specify the *operating system* that the code is running on, as "operating system: *your OS*" as 'mac', 'linux' or 'windows'
This is mainly important if you run the stimulus on a mac, as the size of the stimulus needs to be adjusted in that case.

You can change the *task parameters* in the settings file under "Task settings:"
- you can specify how much time you allow for the participant to respond that still counts as correct response (default is 0.8s), as "response interval: *your time*"
- you can specify the timing of the color switches (default is 3.5s), as "color switch interval: *your interval*"
Note: Make sure that the difference between two adjacent color switches is bigger than the time you give the participant to respond. 
The code adds a randomization of max. +1 or -1 to the color switch times, so e.g. in case of a color switch interval of 3.5, the two closest adjacent color switches will be 1.5s apart, well outside the response interval of 0.8s.



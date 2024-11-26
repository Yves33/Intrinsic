Introduction:
-------------
Intrinsic is a set of automated routines to analyze patch clamp recordings. In its present state, the software can automatically analyse *MY protocols* and those currently used in A.Frick's lab. It will SURELY fail with other files, but it should be easy to adapt it to your protocols.

Currently implemented analysis:
-------------------------------
* IV-curve
* Resistance pulse
* Time constant (positive and negative)
* AHP (all variants)
* Spontaneous activity (CC only)
* resonnance frequency and impedence
* rheobase (yves - abf only)
* ramp (yves, abf only, symetric)

Quick TODO list:
----------------
[ ] write a propper manual. WIP
[ ] load analysis results from @itsq/filename.itsq
[ ] explore use of numba to speed up spike detection
[ ] use min/max downsampling for large traces (spontaneous) analysis:
	https://stackoverflow.com/questions/54449631/improve-min-max-downsampling
	https://github.com/anthonytw/downsample
	actually not a huge speed improvement, but my implmentation remains naïve
[ ] explore use of cuSignal (https://medium.com/rapids-ai/gpu-accelerated-signal-processing-with-cusignal-689062a6af8)
[-] implement synaptic analysis (probably won't fit in the general processing workflow of the program)
	https://github.com/alimuldal/PyFNND
	https://github.com/liubenyuan/py-oopsi/blob/master/README.md
[ ] in experiment. implement export to matlab while saving protocol (either in abf or axgd format)

Installation:
=============
General instructions:
---------------------
The program is written in python >3.8 and requires the following modules:  
`wxpython, numpy, pandas matplotlib,scipy, python-neo, openpyxl, jsonpickle` 

Installation (Linux, stock python):  
-----------------------------------
Open Terminal and run (without ">" character)
```
>pip3 install numpy pandas matplotlib scipy
>pip3 install wxpython python-neo openpyxl jsonpickle 
>python intrinsic_gui.py
```

Installation (Linux, Anaconda3/miniconda3):
-------------------------------------------
1) Download and install Anaconda3/miniconda. I ususally install to $HOME
2) open terminal and run (without ">" char; answer yes when promted):  
```
>conda create -n ephy -c conda-forge --clone base 
>conda activate ephy
>conda install -c conda-forge numpy pandas matplotlib scipy
>conda install -c conda-forge wxpython python-neo openpyxl jsonpickle
>python intrinsic_gui.py
```

Installation (Windows 10, Anaconda3/miniconda3):
------------------------------------------------
procedure tested on win10 x86_64, virtual machine
1) Download anaconda or miniconda
2) Install anaconda. Using default options is ok
* just for me (default)
* do not check Add Anaconda3 to my PATH environnement variable (default)
* check Register anaconda3 as my default Python (default)
3) When done, go to start menu and launch Anaconda Prompt
4) Enter the following commands, excluding ">" sign (y when prompted).

```
>conda init
>conda init powershell
>conda create -n ephy -c conda-forge --clone base
>conda activate ephy
>conda install -c conda-forge python-neo matplotlib scipy openpyxl pandas jsonpickle wxpython
```
5) Ensure that everything is working. Enter the following commands (adjust to intrisic-x.y path).
You should see the main window popup
```
>chdir C:\path\to\intrisiq-x.y
>python intrinsic_gui.py
```

6) At the root of the instrisiq-x.y, double clicking the file win_start.bat should run intrinsic, provided that Anaconda/miniconda is installed in default location (%userprofile%).
You may need to edit the file to reflect your anaconda environement path. Your win_start.bat file should look like this:
```
@echo on    
set PATH=%PATH%;%userprofile%\Anaconda3\Scripts
rem %windir%\system32\cmd.exe "/K" %userprofile%\Anaconda3\Scripts\activate.bat ephy & python intrinsic_gui.py
call %userprofile%\Anaconda3\Scripts\activate.bat ephy
python intrinsic_gui.py
```

Visual code setup (Windows 10, Anaconda3/miniconda3):
----------------------------------------------------
Visual code cannot activate conda environnement from powershell (at least that's what MS tells us). I found that the following procedure works on a fresh win10 x86_64 install (virtual machine).  
1) Download and install vscode from code.visualstudio.com
use default values while installing.
2) Start visual studio. In left panel bar, choose the extension icon (the 4 squares). In popular, install Python (intellisense)
3) Select open folder and navigate to intrisic-xx folder and choose open (or select)
4) In the left panel of visual code, click on intrinsic_gui.py
visual code will suggest you to install the recommended extensions for python, in case you did not already. Click install.  
5) In left panel, click top icon (the two files) and select again intrinsic_gui.py
6) Press ctrl+shift+p. In small popup window on top, enter 'Python' and navigate to "Python: Select interpreter". You should be able to choose different interpreters. Choose the one corresponding to your ephy environnement.  
8) Click on run arrow
9) If visualcode raises an error complaining about execution policy,
enter  the following command in terminal window:
`Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy remotesigned`
Restart terminal (terminal->new terminal). Yous terminal should now display the conda env (base) or (ephy)
10) If visual code complains about not finding conda command, make sure that you run at least one `conda init powershell` in a powershell
conda window, as mentionned in installation. (start menu->Anaconda3->Powershell(base) and enter `conda init powershell`

Installation (OSX, stock python. Not fully tested):
---------------------------------------------------

1) The python interpreter that is (was?) bundled with OSX may be version 2.x. Intrisic requires python >3.8. Using Anaconda turns out to be incredibly slow and hard to setup with wx. I recommand using stock python. 
Download and install
https://www.python.org/downloads/

2) Start a terminal and enter the following commands:
```
>pip3 install numpy pandas matplotlib scipy
>pip3 install wxpython python-neo openpyxl jsonpickle 

```

3) You can lauch the program with Right click on intrinsic_gui.py and choose open with -> Python Launcher


Brief (very) manual (outdated):
====================
Drop files (.axgd or .axgx) to the top of the window, and click on the green gear button.
the GUI has several tabs:
** the main tab is the results (grid)
** the other tabs are generic and protocol specific configuration files.
There are several configuration files which are all located in params folder
each time the software process a *file*
- it saves the current parameters, visible in parameters tabs, to their respective files 
- it reads the generic parameter file generic_params.py (default parameter file is only read at program startup)
- it reads the protocol name from axograph file.
- it tries to read a specific parameter file for that protocol, by looking at a file named <protocol>_params.py.
The local parameters overwrite the generic parameters.(I recommend not modifying default_params, but rather to overwrite them in generic_params_xxx.py)

When the program has finished, it generates up to three files named results.{csv/json/xlsx}. If the appropriate options are set, data are copied to clipboard (stopped working for some unknown reason)

Inputs:
=======
The program is conceived to work with:
- individual axgx and axgd files (drag drop)
- folders containing individual axgx and axgd files. Each folder represents one cell. If the same protocol was recorded several times for one cell, only the *last* one will be taken into account.
- folder containing subfolders containing individual axgx and axgd files. Each subfolder is treated a neuron
- files starting with an underscore or a dot are ignored (configurable with ITSQ_SKIP_FILES global option)

Parameters:
===========
most parameters should be self explanatory (the generic_params file is heavily commented). Just a few notes:
the program recognises which analyses to run by looking at the protocol name, which is encoded in the .axgx .axgd files.
the association is stored in the variables:
IV_PROTOCOL_NAMES, AHP_PROTOCOL_NAMES, TC_PROTOCOL_NAMES, ZAP_PROTOCOL_NAMES,SPONTANEOUS_PROTOCOL_NAMES,...

all config options **must** fit on one line

the program outputs a series of parameters which may differ from one cell to another depending on the protocols that could be run.
in order to always generate the same outputs in the same order, 
if the param ITSQ_OUTPUT_FIELDS_FILE represents a path to a file, the program will read that file and attempt to keep the same order for parameters. parameters starting with - or # are discarded. other parameters are stripped from their optionnal '+' sign. 
If the file does not exist, the program attempts to recreate this file by reading all values provided by each protocol mentionned in PROCESS_PROTOCOLS variable
If ITSQ_OUTPUT_FIELDS_FILE is set to False, it will ignore parameters filtering

Bugs:
=====
There will be bugs. 
There is little error checking:
- The program crashes if it fails to find a frame with IV_MIN_SPIKES spikes of more
- The program crashes if the firing is so high that it cannot detect the threshold. (this can be solved playing with the IV_SPIKE_THRESHOLD1 IV_SPIKE_THRESHOLD2).

Final word:
==========
The current version of the program will work in all tested configurations, and with all available test files!
Obviously, there are many unknown configurations and many unknown files...

Pending bugs:
============
+ icons in toolbar are not always displayed using Qt5/4Agg. I don't know how, I don't know why...
+ TC protocol will fail if the ordering of pulses is not correct (i.e 3 negatives, 3 positives) (solved in v5.x)

2023/03/20:
===========
**new features**
- implemented custom parameters parsing from cfg file for IV_

**internals**
- limited the number of splits with '=' sign in cfg parser. was required to implement custom measurements. 
(so that we can write PARAM="[f.current for f in self.frames if f.current==-100][0]")


2023/03/10:
===========
**new features**
- backported abf2 protocol parser from v5
- in SAG protocol, the number of repeats is now automatically parsed from protocol file

**internals**
- the regexp for parsing number of AP and frequency from AHP protocol names have changed. theyr should be more robust
- implemented segmented signal average

2023/02/24:
===========
**new features**
- implemented AHP measurements for very old files (3-AP train at different frequencies and 5-AP-trains at different frequencies)
- backported filtering mechanism from v5 (now clicking the "filter" button immediately toggles between thefields that were measured and the fields in outfields)

2023/02/20:
===========
**bugs**
- Formerly, the program expected to find the measured signal in channel 0, and used to complain if unit was not good
The program now looks for first channel with expected units.
- Protocol association with protocol name is now case sensitive (fnmatchcase instead of fnmatch)

2023/02/08:
===========
**bugs**
+ the axograph protocol parser has been corrected (but not sure if new version is more reliable than previous one!)

**new features**
+ the program now outputs the half-width of 3rd spike on first IV frame with at least 3 spikes (IV_third_spike_halh_width)
+ there is now a configuration option to revert signs of AHP and ADP (cfg.AHP_CORRECT_SIGNS)

2022/10/13:
===========
**new features**
+ the program now measures the ratio of half-width between 1st and 3rd spikes on first IV frame with at least 3 spikes (IV_half_width_ratio_3/1)

2022/09/28:
===========
**bugs**
+ The measurement for AHP_{cnt}_{freq}Hz_adp_5ms and AHP_{cnt}_{freq}Hz_adp_10ms has changed. 
The reference is now the baseline! (was previously the last spike peak)

**new features**
+ Manual analysis is enabled in AHP protocol using vertical cursors (requires AHP_CHECK_SPIKE_COUNT=Flase and AHP_CHECK_SPIKE_FREQ=False). 
correct protocol naming is mandatory as the frequency andspike count are parsed from protocol name
+ adp_5ms and adp_10ms are plotted on the graph

2022/06/21:
===========
**bugs**
+ There was a mistake in the path to congig files in process_file. This resulted in wrong parameters for IV curve and resistance after a spontaneous activity protocol had been started.
+ The path to resources is now processed using ps.getcwd() instead of __file__

**new features**
ADP measurements 5ms and 10 ms after last spike in AHP protocols (AHP_XX_YYHz_adp_10ms and AHP_XX_YYHz_adp_5ms)

2022/06/13:
===========
**bugs**
+ restored some files that were accidently moved to synaptic (and not copied)
+ cfg.RES_DEBUG_FRAME was not used and the code used some hard coded value

**new features**
+ implemented sag protocol analysis (cfg.SAG_... parameters)

2022/06/02:
===========
**bugs**
+ cfg.IV_SPIKE_MIN_AMP is now updated when peak (topmost) cursor is moved (previously required to move the amplitude cursor)
+ fixed bug that prevented protocol serialization through picklejson (bug introduced when I moved cursors from fig to protocol)
+ fixed external current recordings for ZAP protocol (some were noisy)

**new features**
+ general: there is now a new button in toolbar to disable output filtering. 
when the button is pressed, the content of ITSQ_OUTPUT_FIELDS_FILE is ignored and all measured parameters are copied to the program.

+ IV protocol now also dumps the properties of first spike in the reference frame.
+ RES protocol now dumps impedence at 0.5 Hz. 
+ RES protocol will attempt to read current from a file named $protocol$.txt (export of the axograph protocol) if current is not recorded in the file; this file has the following structure:
```
time(s)	current (A)
0.00000e-5	0.0000e-12
0.50000e-5	0.12345e-12
(...)
```
+ RES protocol now displays the voltage trace with two cursors to select the region to analyze (some RES protocols have a pre-pulse that should be excluded).
+ RES protocols expects to read cfg.RES_AMPLITUDES=[30,50] and will compute the amplitude of input current. 

**cleanups:**
+ some files were moved from resources to __crap__ folder.
+ documentation moved to docs.

2022/05/24:
===========
**bugs**
+ solved conflicts in event loop when using WXAgg in matplotlib
+ corrected autofit region for IV curve to 80% of peak-injection_start)

**new features**
+ fano factor is now computed for all ivframes with more than 4 spikes (for IVcurves, the fano factor reported in results (IF_fano) is calculated at max firing frequency).

**implementation**
+ frame sampling rate is now stored as frame.sr to ease future manipulation when reloading itsq files.
+ implemented some small utilities to build firing curves (nbspikes=f(injected_current)), average spike shapes and PP trajectories, ...

2022/05/19:
===========
**distribution**
+ intrinsic is now compatible with pyinstaller (~/scripts/generate_win_binary.bat)

**implementation changes**
+ xyfitter now has a version and maxfev parameters in constructor and does not reference to ITSQ_FITTER_VERSION nore ITSQ_MAX_ITERATIONS
+ protocol are now passed a fig defaulting to plt.gcf() (was required to embed protocols in generic wx.Panels)
+ the current figure is returned by protocol.fig(), which should enable using several figs for one protocol
+ cursors are now attached to protocols, avoiding monkey patching matplotlib figure
+ frame._cursors() now returns the newly created cursor
+ deprecated frame._update_local and frame._update_global (which was unused. 

**bug fixes**
+ when specifying either 'WX' or 'WXAgg' backend for matplotlib, the program ran all analysis in non interactive mode. (plt.show(block=True) did not start an event loop

2022/05/16:
===========
**bug fixes**
+ corrected RES_Impeddence to RES_impedence (prevented correct output of impedence value)
+ changed the regex for parsing spike count in AHP protocol (protocols with 5APs are named 5AP-xxHz whereas those with 15 APs are named 15AHP...)

**new features**
+ introduced the possibility to clamp computed frequency in AHP to the nearest valid frequency (if cell TC is toohigh, the peaks may be delayed wchich results in improper frequency calculation for 200Hz freq) (cfg.AHP_NEAREST_FREQUENCY)
+ changed config file naming. The program will now search generic_config_xxx.py and use it as generic config file (overwriteswhat's in default). backup folder will be suppressed soon



2022/05/08:
===========
**bug fixes**
+ fixed typo that prevented opening axgx files

**new features**
+ AHP protocol ignore any verification and rely on protocol name to parse spike count and frequency (cfg.AHP_CHECK_NONE.cfg.AHP_SPIKE_START)
+ intrinsic now tries to correct between nA and pA when reading axgd/axgx protocol (cfg.ISTQ_ENABLE_HOOKS)
+ implemented dual parameter file. default_params (always read) and generic_params (overrides values in default, read if present)

2022/04/26:
===========
Program version updated to 3.1

**bug fixes**
many. mostly bugs occuring when IV_MIN_SPIKES_FOR_MEASURE==1

**new features**
+ implemented rheobase protocol analysis
+ added movable cursors for ramp analysis
+ config file migrated to ylf settings!
+ some more results (IV_first_spike_delay, IV_avg_thr2ahp)
+ added rudimentary gui for abfutils

2022/04/08:
===========
**new features:**
+ matplotlib backend is now selectable through configuration file (ITSQ_MPL_BACKEND)
+ added a windows shortcut (works with default conda install)
+ started to rewrite documentation and install instructions
+ first upload to github

2022/04/01:
==========
**bug fixes:**
+ now outputs correct number of spikes (previous naming error resulted in np.nan), 
+ now outputs correct number of spikes AHP values (same error)
+ folder name is correctly parsed (replaced stem with name, as some people introduce dots in their folder names
+ average time constant calculated on IV curves is correctly output (forgot to add it to the measured parameters)

**new features:**
+ AHP measurements stops 50ms after onset of last spike (configurable in generic_params.py)

**cleanups:**
+ removed (some) deprecated params in generic_params.py

2022/03/27:
==========
**Complete program reorgnaisation/rewrite.**
+ each analysis is comprised of two base classes deriving grom genericprotocol and genericfame
+ buttons and user controls have moved to main toolbar (which is by the way very buggy!)

Program version updated to 3.0

**new features:**
+ implemented spontaneous activity protocol
+ implemented resistance protocol
+ implemented simple pulse protocol parsing for abf and axgx/axgd files (with some hacks to guess if units are nA or pA)
+ implemented analysis saving to jsonpickle files @itsq for later reprocessing
+ implemented flexible folder name parsing
+ implemented matlab files reading (for merging IVcurves)
+ implemented multiprocessing for spike analysis (linux, win)

**deprecated features:**
+ fitting time constant of averaged epsc is deprecated. This analysis is now directly performed in mini
+ json files are not parsed anymore (may be reintroduced in later versions)

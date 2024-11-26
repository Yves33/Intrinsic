## parameters for IV curve analysis. Units are Volts and seconds
#########################################################################
## THESE PARAMETERS OVERWRITE DEFAULT PROGRAM VALUES.
#########################################################################
##
ITSQ_LOG_LEVEL=15                                       ## log level DEBUG=10 INFO=20 WARNING=30,ERROR=40 CRITICAL=50
ITSQ_PANZOOM_WHEEL_ONLY=True                            ## should be True
ITSQ_FIT_ITERATION_COUNT=2500                           ## maximum number of iterations for curve fitting 250-10000
ITSQ_FITTER_VERSION=1                                   ## 1 or 2. 2 sometimes gives weird results
ITSQ_OUTPUT_FIELDS_FILE="./params/outfields.txt"        ## list of parameters that the program should output. automatically regenerated if absent. set to False to ignore filtering
ITSQ_SKIP_FILES=['.','_']                               ## skip files starting with one of these characters
ITSQ_ENABLE_MULTIPROCESSING=True                        ## enable parallel processing for spontaneous and iv. Not a major improvement! May not work on some platforms (win, osx)
ITSQ_PROTOCOL_SAVE_DATA=True                            ## save analysis data for each protocol. not tested on OSX. WIP
ITSQ_PARSE_PROTOCOLS=True                               ## parse protocols for current pulses. not heavily tested experimental. works with IV, resistance and mb time constant
ITSQ_MPL_BACKEND="WXAgg"                                ## force matplotlib backend None (auto) or one of 'GTK3Agg', 'MacOSX', 'Qt4Agg', 'Qt5Agg', 'TkAgg', 'WXAgg'; using WXAgg saves resources, but may conflict with internal app event loop
#
EPSILON=0.001                                           ## slight offset between and current injection offsets and offsets for measurement. currently unused

## parameters for IV curve analysis
IV_CURRENT_INJECTION_START=0.1                          ## current injection start time. ususally 0.1 or 0.2      
IV_CURRENT_INJECTION_STOP=0.9                           ## current injection stop time ususally 0.9 or 1., or @IV_CURRENT_INJECTION_START+1.0
IV_BASELINE_START=0.0                                   ## baseline measurement start usually 0
IV_BASELINE_STOP=@IV_CURRENT_INJECTION_START-0.01       ## baseline measurement stop
IV_SAG_PEAK_START=@IV_CURRENT_INJECTION_START+0.01      ## start of sag peak measurement region
IV_SAG_PEAK_STOP=@IV_CURRENT_INJECTION_START+0.20       ## end of sag peak measurement region
IV_SAG_SS_START=@IV_CURRENT_INJECTION_STOP-0.3          ## start of sag stead ystate measurement region
IV_SAG_SS_STOP=@IV_CURRENT_INJECTION_STOP-0.01          ## end of sag stead ystate measurement region
IV_SAG_SS_TARGET_VOLTAGE=0.015                          ## sagratio will be measured for the frame for which sag steady state is the closest of this value (in V)
IV_SAG_TARGET_CURRENT=-100                              ## sagratio for injected current value
IV_TCFIT=True                                           ## calculte mb time constant in IV curve
IV_TCFIT_START=@IV_CURRENT_INJECTION_START+0.00025      ## where to start the membrane time constant fit
IV_TCFIT_STOP=@IV_CURRENT_INJECTION_START+0.2           ## where to stop the membrane time constant fit. if -1, will use sag peak time
IV_TCFIT_AUTOSTOP=True                                  ## automatically guess the end of the fit period (at first analyse)
IV_TCFIT_ORDER=2                                        ## fit with single (1) or double (2) exponential
IV_TCFIT_WEIGHTED_AVERAGE=True                          ## compute weighted average instead of arithmetic average
IV_TCFIT_THRESHOLD=-50                                  ## don't fit frames when injected current is less than
IV_TCFIT_R2_THRESHOLD=0.80                              ## don't accept fits with r2 coeff lower than this value (ignored)
IV_CURRENT_STEPS=[-200+20*i for i in range(26)]         ## list of current steps applied during IV protocol
IV_SPIKE_MIN_PEAK=-0.01                                 ## absolute spike peak votage! spikes that do not cross this threshold will be ignored!
IV_SPIKE_MIN_AMP=0.020                                  ## spike amplitude. more or less the minimum voltage variation betwen threshold and peak
IV_SPIKE_MIN_INTER=0.005                                ## minimum interval between two spikes
IV_SPIKE_PRE_TIME=0.005                                 ## time to keep before spike peak for threshold and maxrise measurement; 0.0015 is ususally enough
IV_SPIKE_POST_TIME=0.01                                 ## time to keep after spike peak for halfwidth measurement;0.005 may be required for correct phase plane analysis
IV_SPIKE_DV_THRESHOLD=0.0002                            ## threshold for first derivative, in case first threshold failed, in V/s. 10 is a good value
IV_SPIKE_LOWEST_THRESHOLD=True                          ## determines two thresholds, based on first and second derivative,and take lowest (otherwise the second threshold is used if threshold detection with 2nd derivative failed )
IV_SPIKE_EVOKED_THRESHOLD=0                             ## for a spike to be considered as evoked, current must be >= to this value. use 0.000001 to eliminate spontaneous spikes
IV_MIN_SPIKES_FOR_MEASURE=4                             ## minimum number of spikes in a frame to measure the threshold,maxrise, ...
IV_MAX_SPIKES_FOR_MEASURE=2000                          ## maximum number of spikes in a frame to measure the thresholds,maxrise, ...
IV_MIN_SPIKES_FOR_SFADAPT=4                             ## number of spikes required to compute spike frequency adaptation
IV_DEBUG_FRAME=True                                     ## display each iv frame

## parameters for AHP analysis
AHP_SS_START=0.0                                        ## start of baseline region for AHP measurement
AHP_SS_STOP=0.05                                        ## end of basline region for AHP measurements 
AHP_SPIKE_MIN_PEAK=0.1                                  ## absolute peak voltage for peak detection
AHP_SPIKE_MIN_AMP=0.050                                 ## minimal amplitude of peak for detection 
AHP_SPIKE_AUTO=True                                     ## determine automagically parameters for peak detection
AHP_MIN_SPIKE_COUNT=3                                   ## minimal number of spikes to count before rejecting a file. if n_spikes<AHP_MIN_SPIKES_COUNT then reject
AHP_MAX_DELAY=0.4                                       ## maximal delay after last identified spike to measure AHP  
AHP_TIME_WINDOW_AVERAGE=0.0002                          ## width (in s) of the window surrounding maximum negative deflection after  last spike
AHP_CHECK_SPIKE_COUNT=True                              ## check wether AHP files should have 5 or 15 APs. otherwise just take the first and last spikes to define baseline and AHP measurement regions. This parameter should be True
AHP_CHECK_SPIKE_FREQ=True                               ## reject frame if computed frequency does not match
AHP_CHECK_NONE=False                                    ## do not check anything. just measure. overwrites AHP_CHECK_SPIKE_COUNT and AHP_CHECK_SPIKE_FREQ
AHP_DEBUG_FRAME=True                                    ## display ahp frame
AHP_VALID_COMBO=[(5,20),(5,40),(5,60),(5,80),(5,100),(5,120),(5,200),(15,20),(15,50)]  ## used to generate the list of AHP output fields

## parameters for mb time constant analysis
TC_FIT_START=0.0510                                     ## start of fit region for mb time constant.
TC_FIT_STOP=@TC_FIT_START+0.04                          ## end of fit region for mb time constant
TC_FIT_CURRENT_STEPS=[-400,-400,-400,400,400,400]       ## injected current. currently not used
TC_FIT_ORDER=2                                          ## fit with simple, double or triple exponential (1,2,3)
TC_WEIGHTED_AVERAGE=True                                ## take the weighted average of the two time constants, otherwise arithmetic average             
TC_DEBUG_FRAME=True                                     ## display tc frame

## parameters for résonnance analysis
RES_LOW_BAND=0.01                                       ## start of band pass
RES_HIGH_BAND=10                                        ## end of band pass
RES_AMPLITUDES=[30,50]                                  ## list of allowed amplitudes for resonnance protococols
RES_DEBUG_FRAME=True                                    ## display resonnance frame

## parameters for resistance analysis
INPUTR_CURRENT_INJECTION_START=0.2                      ## start of current injection (seconds)
INPUTR_CURRENT_INJECTION_STOP=0.7                       ## end of current injection (seconds)
INPUTR_CURRENT_STEP=-20                                 ## current step amplitude (pA)
INPUTR_TCFIT_START=@INPUTR_CURRENT_INJECTION_START+0.01 ## start of exponential fit
INPUTR_TCFIT_STOP=@INPUTR_CURRENT_INJECTION_STOP-0.01   ## end of exponential fit             
INPUTR_TCFIT_ORDER=2                                    ## fitting order for exp
INPUTR_TCFIT_WEIGHTED_AVERAGE=True                      ## take the weighted average of the two time constants, otherwise arithmetic average
INPUTR_DEBUG_FRAME=True                                 ## display averaged frames

## parameters for spontaneous activity (current clamp. spikes)
SPONTANEOUS_DEBUG_FRAME=True                            ## display spontaneous activity frame

## parameters for ramp
RAMP_BOUNDARIES=[0.13,1.13,1.21,2.21]                   ## the regions for Ramp
RAMP_DEBUG_FRAME=True                                   ## display ramp frames

## parameters for folder naming
##FOLDER_NAMING_SCHEME='WTC1  -V2.1-12w-A1     -DIV21 -2022.03.01-Cell1
FOLDER_NAMING_SCHEME='animal-behavior-labelling-number'   ## sceme for folder naming
FOLDER_NAMING_SEP='-'                                     ## separator for fields in folder name

## process flags
PROCESS_PROTOCOLS=['foldername','iv','resistance','spontaneousactivity','timeconstant','ahp','resonnance','ramp']
PROCESS_EXTENSIONS=['.axgx','.axgd','.abf','.maty']

## output parameters for csv,excel,json
OUTPUT_CSVSEP="\t"                                      ## the separator for fields, ususally comma (',') for csv or tab ('\t') for tsv
OUTPUT_CSV=True
OUTPUT_JSON=True
OUTPUT_EXCEL=True
OUTPUT_CLIPBOARD=True                                   ## output should also be pasted to clipboard
OUTPUT_CLIPBOARD_EXCEL=True                             ## clipboard should be formatted for excel
OUTPUT_CLIPBOARD_ROWNAMES=False                         ## clipboard should include row names

## scale factors. SI values are **divided** by these values
## The program caculates everything SI (V,A,s,Ohm,F)
OUTPUT_V_SCALE=1e-3                  ## use 1e-3 to convert V to mV          (0,003V             -> 3mV)
OUTPUT_OHM_SCALE=1e6                 ## use 1e6 to convert Ohms to MOhms     (450,235,123.00Ohms -> 450,23Mohms)
OUTPUT_S_SCALE=1e-3                  ## use 1e-3 to convert s to ms          (0.1s               -> 100ms)
OUTPUT_A_SCALE=1e-12                 ## use 1e-12 to convert A to pA         (0.000 000 000 153A -> 153pA)
OUTPUT_F_SCALE=1e-12                 ## use 1e-12 to convert F to pF         (0.000 000 000 256F -> 256pA)

## protocol names
## much fun here: different names for the "not so" different protocols with strictly identical analysis, depending on the setups...
## for analysis, provide a list of all protocol names that should match a given analysis
## each value is tested as an fnmatch string (? stands for any caracter, * for any suite of caracters, [Tt] any character in group)
IV_PROTOCOL_NAMES=['IV_multiclamp','3-IV curve','*CCSteps*','*IV*']
AHP_PROTOCOL_NAMES=['*5AP*',"*AHP*"]
TC_PROTOCOL_NAMES=['*[Tt]ime constant*',]
ZAP_PROTOCOL_NAMES=['*ZAP*', 'resonnance']
INPUTR_PROTOCOL_NAMES=['*resistance*']
SPONTANEOUS_PROTOCOL_NAMES=['*[Ss]pontaneous*']
RAMP_PROTOCOL_NAMES=['*ramp*']

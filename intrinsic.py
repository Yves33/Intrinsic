#!/usr/bin/env python3
# Copyright (c)2020-2022, Yves Le Feuvre <yves.le-feuvre@u-bordeaux.fr>
#
# All rights reserved.
#
# This file is prt of the intrinsic program
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted under the terms of the BSD License. See
# LICENSE file in the root of the Project.

## Python stdlib import. Can't live without it
from cmath import nan
import os,sys,platform,logging,fnmatch,pprint,re,time
sys.path.insert(0,"./modules")
from pathlib import Path

import warnings
warnings.filterwarnings('ignore')
warnings.warn = lambda *args,**kwargs:0   ## shut down matplotlib deprecation warnings

## data science stack
import numpy as np
import pandas as pd
import scipy
import quantities as pq
import neo
import neomonkey
neomonkey.installmonkey()               ## use our custom array access routines

from config import cfg
cfg.parse("./params/default_params.py")
gen_cfg_files=list(Path("./params/").glob("generic_params_*.py"))
if len(gen_cfg_files)!=1:
    logging.getLogger(__name__).critical("More than one generic config file was found!")
    exit(-1)
gen_cfg_file=str(gen_cfg_files[0])
logging.getLogger(__name__).critical(f"Current parameter file {gen_cfg_file}")
if os.path.isfile(gen_cfg_file):
	cfg.parse(gen_cfg_file)
	
prefix={1e-12:'p',
        1e-9:'n',
        1e-6:'µ',
        1e-3:'m',
        1:' ',
        1e3:'k',
        1e6:'M',
        1e9:'G'}
import matplotlib
## tried several backend, but none is clearly faster than another, ecept for gr, but which is very buggy!
'''
'GTK3Agg', 'GTK3Cairo', 'MacOSX', 'nbAgg', 'Qt4Agg', 'Qt4Cairo', 'Qt5Agg', 'Qt5Cairo', 
'TkAgg', 'TkCairo', 'WebAgg', 'WX', 'WXAgg', 'WXCairo', 
'agg', 'cairo', 'pdf', 'pgf', 'ps', 'svg', 'template'
'''
#matplotlib.use("module://gr.matplotlib.backend_gr")
if cfg.ITSQ_MPL_BACKEND in ['GTK3Agg', 'MacOSX', 'Qt4Agg', 'Qt5Agg', 'TkAgg', 'WXAgg']:
    matplotlib.use(cfg.ITSQ_MPL_BACKEND)
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
#plt.rcParams['lines.antialiased']=True
#plt.rcParams['lines.linewidth']=1.0
from mpl_interaction import PanAndZoom
from mpl_toolbutton import TriggerBtn,ToggleBtn
from mpl_draggable import draggable_line

from experiment import Experiment
from xyfitter import XYFitter
from baseprotocol import once,BaseFrame,BaseProtocol
## default config file in case we lose the original one
defaultconfig='''
## parameters for IV curve analysis. Units are Volts and seconds
#########################################################################
## THESE PARAMETERS OVERWRITE DEFAULT PROGRAM VALUES.
#########################################################################
##

ITSQ_VERSION=3.21                                       ## the version of intrinsic that match this param file. No version check is performed, but that may change in a near future
ITSQ_LOG_LEVEL=10                                       ## log level DEBUG=10 INFO=20 WARNING=30,ERROR=40 CRITICAL=50
ITSQ_PANZOOM_WHEEL_ONLY=True                            ## should be True
ITSQ_FIT_ITERATION_COUNT=10000                          ## maximum number of iterations for curve fitting 250-10000
ITSQ_FITTER_VERSION=1                                   ## 1 or 2. 2 sometimes gives weird results
ITSQ_OUTPUT_FIELDS_FILE="./params/outfields.txt"        ## list of parameters that the program should output. automatically regenerated if absent. set to False to ignore filtering
ITSQ_SKIP_FILES=['.','_']                               ## skip files starting with one of these characters
ITSQ_ENABLE_MULTIPROCESSING=True                        ## enable parallel processing for spontaneous and iv. Not a major improvement! May not work on some platforms (win, osx)
ITSQ_PROTOCOL_SAVE_DATA=True                            ## save analysis data for each protocol. not tested on OSX. WIP
ITSQ_PARSE_PROTOCOLS=True                               ## parse protocols for current pulses (only). not heavily tested experimental. works with IV, resistance and mb time constant
ITSQ_MPL_BACKEND=None                                   ## force matplotlib backend None (auto) or one of 'GTK3Agg', 'MacOSX', 'Qt4Agg', 'Qt5Agg', 'TkAgg', 'WXAgg'; using WXAgg saves resources, but may conflict with internal app event loop
ITSQ_ENABLE_HOOKS=True                                  ## guess if current steps are nA or pA and convert to pA. No guarantee! some other hooks may be implemented later
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
IV_SAG_TARGET_CURRENT=-90                               ## sagratio for injected current value
IV_TCFIT=True                                           ## calculate mb time constant in IV curve
IV_TCFIT_START=@IV_CURRENT_INJECTION_START+0.00025      ## where to start the membrane time constant fit
IV_TCFIT_STOP=@IV_CURRENT_INJECTION_START+0.2           ## where to stop the membrane time constant fit. if -1, will use sag peak time
IV_TCFIT_AUTOSTOP=True                                  ## automatically guess the end of the fit period (at first analyse)
IV_TCFIT_ORDER=2                                        ## fit with single (1) or double (2) exponential
IV_TCFIT_WEIGHTED_AVERAGE=True                          ## compute weighted average instead of arithmetic average
IV_TCFIT_THRESHOLD=-25                                  ## don't fit frames when injected current is less than
IV_TCFIT_R2_THRESHOLD=0.80                              ## don't accept fits with r2 coeff lower than this value (ignored)
IV_CURRENT_STEPS=list(range(-95,100,5))                 ## list of current steps applied during IV protocol
IV_SPIKE_MIN_PEAK=-0.01                                 ## absolute spike peak votage! spikes that do not cross this threshold will be ignored!
IV_SPIKE_MIN_AMP=0.020                                  ## spike amplitude. more or less the minimum voltage variation betwen threshold and peak
IV_SPIKE_MIN_INTER=0.005                                ## minimum interval between two spikes
IV_SPIKE_PRE_TIME=0.005                                 ## time to keep before spike peak for threshold and maxrise measurement; 0.0015 is ususally enough
IV_SPIKE_POST_TIME=0.01                                 ## time to keep after spike peak for halfwidth measurement;0.005 may be required for correct phase plane analysis
IV_SPIKE_DV_THRESHOLD=0.0002                            ## threshold for first derivative, in case first threshold failed, in V/s. 10 is a good value
IV_SPIKE_LOWEST_THRESHOLD=True                          ## determines two thresholds, based on first and second derivative,and take lowest (otherwise the second threshold is used if threshold detection with 2nd derivative failed )
IV_SPIKE_EVOKED_THRESHOLD=0                             ## for a spike to be considered as evoked, current must be >= to this value. use 0.000001 to eliminate spontaneous spikes
IV_MIN_SPIKES_FOR_MEASURE=1                             ## minimum number of spikes in a frame to measure the threshold,maxrise, ...
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
AHP_MAX_DELAY=0.5                                       ## maximal delay after last identified spike to measure AHP  
AHP_TIME_WINDOW_AVERAGE=0.0002                          ## width (in s) of the window surrounding maximum negative deflection after  last spike
AHP_CHECK_SPIKE_COUNT=False                             ## check wether AHP files should have 5 or 15 APs. otherwise just take the first and last spikes to define baseline and AHP measurement regions. This parameter should be True
AHP_CHECK_SPIKE_FREQ=False                              ## reject frame if computed frequency does not match
AHP_CHECK_NONE=False                                    ## do not check anything. just measure. overwrites AHP_CHECK_SPIKE_COUNT and AHP_CHECK_SPIKE_FREQ
AHP_SPIKE_START=0.1                                     ## onset of first spike. used only if AHP_CHECK_NONE is set
AHP_NEAREST_FREQUENCY=True                              ## clamp the computed frequency to the nearest frequency. usefull for 200Hz frequency, but can be dangerous           
AHP_DEBUG_FRAME=True                                    ## display ahp frame
AHP_VALID_COMBO=[(5,10)]                                ## used to generate the list of AHP output fields

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

## parameters for rheobase
RHEO_CURRENT_INJECTION_START=0.20775
RHEO_CURRENT_INJECTION_STOP=0.25775
RHEO_BASELINE_START=0.0
RHEO_BASELINE_STOP=0.2
RHEO_DEBUG_FRAME=True

## parameters for SAG protocol
SAG_AVERAGE_COUNT=3
SAG_CURRENT_STEPS=[-200,-180,-160,-140,-120,-100,-80,-60,-40,-20,0]
SAG_CURRENT_INJECTION_START=0.1
SAG_CURRENT_INJECTION_STOP=0.9
SAG_DEBUG_FRAME=True


## parameters for folder naming
##FOLDER_NAMING_SCHEME='WTC1  -V2.1-12w-A1     -DIV21 -2022.03.01-Cell1
FOLDER_NAMING_SCHEME='date_cell'                        ## sceme for folder naming
FOLDER_NAMING_SEP='_'                                   ## separator for fields in folder name

## process flags
#PROCESS_PROTOCOLS=['foldername','iv','resistance','spontaneousactivity','timeconstant','ahp','resonnance','ramp','rheobase','sag']
PROCESS_PROTOCOLS=['foldername','iv','resistance','spontaneousactivity','timeconstant','ahp','resonnance','ramp','rheobase','sag']
PROCESS_EXTENSIONS=['.axgd','.axgx','.abf','.maty']

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
IV_PROTOCOL_NAMES=['IV_multiclamp','3-IV curve','*IV*',]
AHP_PROTOCOL_NAMES=['*5AP*','*AHP*',]
TC_PROTOCOL_NAMES=['*constant*',]
ZAP_PROTOCOL_NAMES=['*ZAP*', 'resonnance']
INPUTR_PROTOCOL_NAMES=['*resistance*']
SPONTANEOUS_PROTOCOL_NAMES=['*[Ss]pontaneous*']
RAMP_PROTOCOL_NAMES=['*[Rr]amp*']
RHEO_PROTOCOL_NAMES=['*rheo*']
SAG_PROTOCOL_NAMES=['*[Ss]ag_*']
'''

## some other globals
filecount=0	             ## nummber of files that were processed

######################################################################################
######################################################################################
## BASE and UTITY CLASSES
######################################################################################
######################################################################################
##################
## utility functions
##################
def _pprint(q,unit):
    try:
        if unit==pq.Ohm:
            return f'{q/cfg.OUTPUT_OHM_SCALE:.3f} {prefix[cfg.OUTPUT_OHM_SCALE]}Ohms'
        elif unit==pq.V:
            return f'{q/cfg.OUTPUT_V_SCALE:.3f} {prefix[cfg.OUTPUT_V_SCALE]}V'
        elif unit==pq.s:
            return f'{q/cfg.OUTPUT_S_SCALE:.3f} {prefix[cfg.OUTPUT_S_SCALE]}s'
        elif unit==pq.A:
            return f'{q/cfg.OUTPUT_A_SCALE:.3f} {prefix[cfg.OUTPUT_A_SCALE]}A'
        elif unit==pq.F:
            return f'{q/cfg.OUTPUT_F_SCALE:.3f} {prefix[cfg.OUTPUT_F_SCALE]}F'
    except:
        return "nan"

def _autoscale(ax,x,y,xmargin=0,ymargin=0.1):
    xmargin=0.1*abs(max(x)-min(x))
    ax.set_xlim(min(x),max(x))
    ymargin=0.1*abs(max(y)-min(y))
    ax.set_ylim(min(y)-ymargin,max(y)+ymargin)

def _prefix(stringlist,prefix):
    return [prefix+l for l in stringlist] 

def _clamp(x,lo,hi):
    return max(lo, min(x, hi))

##################################################################################################
##################################################################################################
##################################################################################################
## START OF PROTOCOLS SECTION
##################################################################################################
##################################################################################################
##################################################################################################
'''
    Time Constant Protocol, Frick lab version
    attempts to fit a single of double exponential over Voltage curve
    input:  sigs: list of neo.io.AnalogSignal with units V, mV (units are not checked, so should also work with pA)
    cfg:TC_FIT_START,TC_FIT_STOP,TC_WEIGHTED_AVERAGE,TC_DEBUG_FRAME,OUTPUT_S_SCALE
    usage: protocol=timeconstantprotocol(sig,interactive)
           print(protocol.results())
'''
class tcframe(BaseFrame):
    def __init__(self,sig,idx,parent):
        self.voltage=sig
        self.sr=int(sig.sampling_rate)
        super(tcframe,self).__init__(idx,parent)

    def process(self,bitmask=0xFFFF):
        times=self.voltage.s(cfg.TC_FIT_START,cfg.TC_FIT_STOP)
        volts=self.voltage.V(cfg.TC_FIT_START,cfg.TC_FIT_STOP)
        self.fitter=XYFitter(times,volts,cfg.TC_FIT_ORDER,cfg.TC_WEIGHTED_AVERAGE,cfg.TC_FIT_START,
                            maxfev=cfg.ITSQ_FIT_ITERATION_COUNT,
                            version=cfg.ITSQ_FITTER_VERSION)
        self.fitline=[times,self.fitter.line(times)]
    
    @once
    def setup(self):
        self._fig().subplots(1, 1)
        self._cursor(self._axes(0),'v',cfg.TC_FIT_START,
                    lambda x:cfg.set('TC_FIT_START',x) or self.parent.process(0xFFFF) or self.parent.draw (False))
        self._cursor(self._axes(0),'v',cfg.TC_FIT_STOP,
                    lambda x:cfg.set('TC_FIT_STOP',x) or self.parent.process(0xFFFF) or self.parent.draw (False))

    def draw(self,drawall=True):
        self.setup() ## ensure that axes are ready!
        self._fig().canvas.TopLevelParent.SetTitle("Time constant protocol")
        if drawall:  ## avoid redrawing signals if not required
            self._clf(['traces'])
            self._axes(0).plot(self.voltage.s(), self.voltage.V(),color='blue',gid='traces')
            _autoscale(self._axes(0),self.voltage.s(),self.voltage.V())
        self._clf(['markers'])
        if self.fitter.success:
            self._axes(0).set_title(f'TC: {_pprint(self.fitter.tc,pq.s)}')
            self._axes(0).plot( self.fitline[0], self.fitline[1],color='red',gid='markers')

class timeconstantprotocol(BaseProtocol):
    def __init__(self,sigs,interactive):
        self.frames=[tcframe(s,idx=e,parent=self) for e,s in enumerate(sigs) ]
        super(timeconstantprotocol,self).__init__(interactive)
    def provides(self):
        return {'TC_tc_neg':'avg time constant, measured for negative current pulse',
                'TC_tc_pos':'avg time constant, measured for positive current pulse'}
    def results(self):
        ## np.mean return nan for empty lists
        self.r= {'TC_tc_neg':np.nanmean([f.fitter.tc for f in self.frames if f.fitter.success and f.enabled and f.idx<len(self.frames)/2 ] )/cfg.OUTPUT_S_SCALE,
                'TC_tc_pos':np.nanmean([f.fitter.tc for f in self.frames if f.fitter.success and f.enabled and f.idx>len(self.frames)/2 ] )/cfg.OUTPUT_S_SCALE}
        return self.r
'''
    Sag ratio protocol, Frick lab version (Yukti & Anna)
    steps from -200 to 0 step 20. 3 frames for each current step (averaged frames are passed to protocol)
    fitting time constatnt is disabled in this protocol.
    input: sigs list of neo.io.AnalogSignal with units V, mV (units are not checked)
    currenstep: list of current steps amplitude used for this trace. required to output results
    cfg: SAG_CURRENT_INJECTION_START,SAG_CURRENT_INJECTION_STOP,SAG_CURRENT_STEPS
    usage: protocol=sagprotocol(sigs,interactive,current_steps)
            print(protocol.results)
'''
class sagframe(BaseFrame):
    def __init__(self,sig,currentstep,idx,parent): ## current should not be passed from constructor but rather read from cfg.SAG_CURRENT_STEPS
        self.voltage=sig
        self.sr=int(sig.sampling_rate)
        self.currentstep=currentstep
        super(sagframe,self).__init__(idx,parent)

    def process(self,bitmask=0xFFFF):
        midpoint=0.66*(cfg.SAG_CURRENT_INJECTION_START+cfg.SAG_CURRENT_INJECTION_STOP)
        self.baseline=np.mean(self.voltage.V(0.0,cfg.SAG_CURRENT_INJECTION_START))
        self.steadystate=np.mean(self.voltage.V(midpoint,cfg.SAG_CURRENT_INJECTION_STOP))
        #self.resistance=np.abs((self.baseline-self.steadystate)/self.currentstep*1e12) ##in Ohms current step is in pA 
        #times=self.voltage.s(cfg.SAG_TCFIT_START,cfg.SAG_TCFIT_STOP)
        #volts=self.voltage.V(cfg.SAG_TCFIT_START,cfg.SAG_TCFIT_STOP)
        #self.fitter=XYFitter(times,volts,cfg.SAG_TCFIT_ORDER,cfg.SAG_TCFIT_WEIGHTED_AVERAGE,cfg.SAG_TCFIT_START,
        #                    maxfev=cfg.ITSQ_FIT_ITERATION_COUNT,
        #                    version=cfg.ITSQ_FITTER_VERSION)
        #self.fitline=[times,self.fitter.line(times)]
        negpeak=np.argmin(self.voltage.V())/float(self.voltage._sampling_rate)
        self.sagpeak=np.mean(self.voltage.V(negpeak-0.01,negpeak+0.01))
        self.sagratio=(self.baseline-self.steadystate)/(self.baseline-self.sagpeak)  

    @once
    def setup(self):
        self._fig().subplots(1, 1)
        #self._cursor(self._axes(0),'v',cfg.SAG_TCFIT_START,
        #            lambda x:cfg.set('SAG_TCFIT_START',x) or self.parent.process(0xFFFF) or self.parent.draw ())
        #self._cursor(self._axes(0),'v',cfg.SAG_TCFIT_STOP,
        #            lambda x:cfg.set('SAG_TCFIT_STOP',x) or self.parent.process(0xFFFF) or self.parent.draw ())

    def draw(self,drawall=True):
        self.setup() ## ensure that axes are ready!
        self._fig().canvas.TopLevelParent.SetTitle("Sag protocol protocol")
        if drawall:  ## avoid redrawing signals if not required
            self._clf(['traces'])
            self._axes(0).plot(self.voltage.s(), self.voltage.V(),color='blue',gid='traces')
            _autoscale(self._axes(0),self.voltage.s(),self.voltage.V())
        self._clf(['markers'])
        self._axes(0).set_title(f'Sag ratio {self.currentstep}pA: {self.sagratio} ')
        #if self.fitter.success:
        #    self._axes(0).plot( self.fitline[0], self.fitline[1],color='red',gid='markers')
        self._axes(0).axhline(self.baseline,color="black",linestyle ="--",gid='markers')
        self._axes(0).axhline(self.steadystate,color="grey",linestyle ="--",gid='markers')
        self._axes(0).axhline(self.sagpeak,color="green",linestyle ="--",gid='markers')

class sagprotocol(BaseProtocol):
    def __init__(self,sigs,interactive,currentstep=None):
        self.frames=[sagframe(s,currentstep[e],idx=e,parent=self) for e,s in enumerate(sigs) ]
        super(sagprotocol,self).__init__(interactive)
    def provides(self):
        d={}
        for c in cfg.SAG_CURRENT_STEPS:
            d[f'SAG_ratio_{c}pA']=f'average voltage peak value for {c}pA current step'
        return d
    def results(self):
        d={}
        for f in self.frames:
            d[f'SAG_ratio_{f.currentstep}pA']=f.sagratio
        return d

'''
    Resistance Protocol, Frick lab version
    attempts to fit a single of double exponential over Voltage curve and measures resistance
    input:  sigs: array of neo.io.AnalogSignal with units V, mV (units are not checked)
    currentstep: the value of the current step
    results:Resistance_avg_pulse,Time_constant_average_pulse
    cfg:INPUTR_CURRENT_INJECTION_START,INPUTR_CURRENT_INJECTION_STOP,INPUTR_WEIGHTED_AVERAGE,INPUTR_FIT_ORDER,OUTPUT_S_SCALE,OUTPUT_OHM_SCALE
    usage: protocol=resistanceprotocol(sig,interactive)
           print(protocol.results())
'''
class resistanceframe(BaseFrame):
    def __init__(self,sig,currentstep,idx,parent):
        self.voltage=sig
        self.sr=int(sig.sampling_rate)
        self.currentstep=currentstep
        super(resistanceframe,self).__init__(idx,parent)

    def process(self,bitmask=0xFFFF):
        midpoint=0.66*(cfg.INPUTR_CURRENT_INJECTION_START+cfg.INPUTR_CURRENT_INJECTION_STOP)
        self.baseline=np.mean(self.voltage.V(0.0,cfg.INPUTR_CURRENT_INJECTION_START))
        self.steadystate=np.mean(self.voltage.V(midpoint,cfg.INPUTR_CURRENT_INJECTION_STOP))
        self.resistance=np.abs((self.baseline-self.steadystate)/self.currentstep*1e12) ##in Ohms current step is in pA 
        times=self.voltage.s(cfg.INPUTR_TCFIT_START,cfg.INPUTR_TCFIT_STOP)
        volts=self.voltage.V(cfg.INPUTR_TCFIT_START,cfg.INPUTR_TCFIT_STOP)
        self.fitter=XYFitter(times,volts,cfg.INPUTR_TCFIT_ORDER,cfg.INPUTR_TCFIT_WEIGHTED_AVERAGE,cfg.INPUTR_TCFIT_START,
                            maxfev=cfg.ITSQ_FIT_ITERATION_COUNT,
                            version=cfg.ITSQ_FITTER_VERSION)
        self.fitline=[times,self.fitter.line(times)]
        negpeak=np.argmin(self.voltage.V())/float(self.voltage._sampling_rate)
        self.sagpeak=np.mean(self.voltage.V(negpeak-0.01,negpeak+0.01))
        self.sagratio=(self.baseline-self.steadystate)/(self.baseline-self.sagpeak)  

    @once
    def setup(self):
        self._fig().subplots(1, 1)
        self._cursor(self._axes(0),'v',cfg.INPUTR_TCFIT_START,
                    lambda x:cfg.set('INPUTR_TCFIT_START',x) or self.parent.process(0xFFFF) or self.parent.draw ())
        self._cursor(self._axes(0),'v',cfg.INPUTR_TCFIT_STOP,
                    lambda x:cfg.set('INPUTR_TCFIT_STOP',x) or self.parent.process(0xFFFF) or self.parent.draw ())

    def draw(self,drawall=True):
        self.setup() ## ensure that axes are ready!
        self._fig().canvas.TopLevelParent.SetTitle("Resistance protocol")
        if drawall:  ## avoid redrawing signals if not required
            self._clf(['traces'])
            self._axes(0).plot(self.voltage.s(), self.voltage.V(),color='blue',gid='traces')
            _autoscale(self._axes(0),self.voltage.s(),self.voltage.V())
        self._clf(['markers'])
        self._axes(0).set_title(f'Res : {_pprint(self.resistance,pq.Ohm)} '+\
                           f'TC: {_pprint(self.fitter.tc,pq.s)}')
        if self.fitter.success:
            self._axes(0).plot( self.fitline[0], self.fitline[1],color='red',gid='markers')
        self._axes(0).axhline(self.baseline,color="black",linestyle ="--",gid='markers')
        self._axes(0).axhline(self.steadystate,color="grey",linestyle ="--",gid='markers')
        self._axes(0).axhline(self.sagpeak,color="green",linestyle ="--",gid='markers')

class resistanceprotocol(BaseProtocol):
    def __init__(self,sigs,interactive,currentstep=None):
        self.frames=[resistanceframe(s,currentstep,idx=e,parent=self) for e,s in enumerate(sigs) ]
        super(resistanceprotocol,self).__init__(interactive)
    def provides(self):
        return {'INPUTR_res':'avg input resistance',
                'INPUTR_tc':'avg time constant',
                'INPUTR_baseline':'avg baseline before current pulse',
                'INPUTR_sagratio':'avg sag ratio'}
    def results(self):
        self.r= {'INPUTR_res':np.nanmean([f.resistance for f in self.frames if f.enabled ] ) / cfg.OUTPUT_OHM_SCALE,
                'INPUTR_tc':np.nanmean([f.fitter.tc for f in self.frames if f.fitter.success and f.enabled ] ) / cfg.OUTPUT_S_SCALE,
                'INPUTR_baseline':np.nanmean([f.baseline for f in self.frames if f.fitter.success and f.enabled]) / cfg.OUTPUT_V_SCALE,
                'INPUTR_sagratio':np.nanmean([f.sagratio for f in self.frames if f.fitter.success and f.enabled])}
        return self.r

'''
    AHP protocol, Frick lab version
    measures the AHP after last spike in a series of 5 or 15 spikes at distinct frequencies
    input:  sigs: array of neo.io.AnalogSignal with units V, mV (units not checked)
    freq: the frequency of spike trains. if none, the program tries to guess
    cfg:AHP_SS_START, AHP_SS_STOP, AHP_SPIKE_MIN_PEAK, AHP_SPIKE_MIN_AMP, AHP_TIME_WINDOW_AVERAGE,AHP_IGNORE_SPIKE_COUNT,AHP_IGNORE_FREQUENCY_CHECK
    usage: protocol=ahpprotocol(sig,interactive)
           print(protocol.results())
'''
class ahpsimpleframe(BaseFrame):
    def __init__(self,sig,frequency,apcount,idx,parent):
        logging.getLogger().info("Using new simplified AHP analysis")
        self.voltage=sig
        self.sr=int(sig.sampling_rate)
        self.frequency=frequency
        self.apcount=apcount
        self.ahp_value=None
        self.ahp_value_1s=None
        self.adp_5ms=None
        self.adp_10ms=None
        self.p1=0.1
        self.p2=0.2
        if cfg.AHP_SPIKE_AUTO:
            hi,lo=np.max(self.voltage.V()),np.min(self.voltage.V())
            delta=(hi-lo)
            cfg.AHP_SPIKE_MIN_PEAK=lo+delta*0.5
            cfg.AHP_SPIKE_MIN_AMP=delta*0.35
        super(ahpsimpleframe,self).__init__(idx,parent)

    def process(self,bitmask=0xFFFF):
        self.baseline=float(np.mean(self.voltage.V(cfg.AHP_SS_START,cfg.AHP_SS_STOP)))
        volts=self.voltage.V()
        times=self.voltage.s()
        ## working in samples, as we're using find_peaks and argmin
        peak_pos,peak_info=scipy.signal.find_peaks(volts, \
                                    height=cfg.AHP_SPIKE_MIN_PEAK,\
                                    prominence=cfg.AHP_SPIKE_MIN_AMP,\
                                    distance=int(0.00040*self.voltage._sampling_rate)) # up to 200Hz
        validcounts=set([cnt for cnt,freq in cfg.AHP_VALID_COMBO])
        validfreqs=set([freq for cnt,freq in cfg.AHP_VALID_COMBO])
        if len(peak_pos)==0:
            logging.getLogger().error("Could not find any peak in data!")
            self.ahp_pos=np.nan
            self.ahp_value=np.nan
            self.ahp_pos_1s=np.nan
            self.ahp_value_1s=np.nan
            self.adp_5ms=np.nan
            self.adp_5ms_t=np.nan
            self.adp_10ms=np.nan
            self.adp_10ms_t=np.nan
            return
        
        self.peakcount=self.apcount
        self.peaks={'x':times[peak_pos],'y':volts[peak_pos]}
        ## get the mimimum
        self.ahp_pos=peak_pos[-1]+np.argmin(  volts[peak_pos[-1] : peak_pos[-1] + int(cfg.AHP_MAX_DELAY*self.voltage.sampling_rate) ] )
        start=int(self.ahp_pos-cfg.AHP_TIME_WINDOW_AVERAGE*int(self.voltage.sampling_rate))
        stop=int(self.ahp_pos+cfg.AHP_TIME_WINDOW_AVERAGE*int(self.voltage.sampling_rate))
        self.ahp_value=self.baseline-np.mean(volts[start:stop]) ##self.baseline-np.mean(self.voltage.V(start,stop)) works also, as start and stop are int
        ## Anna's request.
        ## was previously measured relative to last spike max. now relative to baseline
        ## bounds checking is required here!
        try:
            self.adp_5ms =self.baseline-volts[ peak_pos[-1]+int( 5e-3*int(self.voltage.sampling_rate))]
            self.adp_5ms_t =peak_pos[-1]/float(self.voltage.sampling_rate)+5e-3
        except:
            self.adp_5ms =np.nan
            self.adp_5ms_t =np.nan
        try:
            self.adp_10ms=self.baseline-volts[ peak_pos[-1]+int(10e-3*int(self.voltage.sampling_rate))]
            self.adp_10ms_t=peak_pos[-1]/float(self.voltage.sampling_rate)+10e-3
        except:
            self.adp_10ms=np.nan
            self.adp_10ms_t=np.nan
        ## if we succeeded, place vertical cursors accordingly
        ## frames are created before protocol. hence cursors may not be created here
        try:
            self._get_cursor(2).setpos(peak_pos[-1]/self.voltage.sampling_rate)
            self._get_cursor(3).setpos(self.ahp_pos/self.voltage.sampling_rate)
        except:
            pass
        ## get the value 1s after last peak
        try:
            self.ahp_pos_1s=peak_pos[-1]+int(1.0*self.voltage.sampling_rate)
            start=int(self.ahp_pos_1s-cfg.AHP_TIME_WINDOW_AVERAGE*int(self.voltage.sampling_rate))
            stop=int(self.ahp_pos_1s+cfg.AHP_TIME_WINDOW_AVERAGE*int(self.voltage.sampling_rate))
            self.ahp_value_1s=self.baseline-np.mean(volts[start:stop])
        except:
            self.ahp_pos_1s=np.nan
            self.ahp_value_1s=np.nan

    def manualprocess(self,bitmask=0xFFFF):
        ## much easier...
        self.baseline=float(np.mean(self.voltage.V(cfg.AHP_SS_START,cfg.AHP_SS_STOP)))
        volts=self.voltage.V()
        p1=int(self.p1*self.voltage.sampling_rate)
        p2=int(self.p2*self.voltage.sampling_rate)
        self.ahp_pos=p1+np.argmin(volts[p1 : p2 ])
        start=int(self.ahp_pos-cfg.AHP_TIME_WINDOW_AVERAGE*int(self.voltage.sampling_rate))
        stop=int(self.ahp_pos+cfg.AHP_TIME_WINDOW_AVERAGE*int(self.voltage.sampling_rate))
        self.ahp_value=self.baseline-np.mean(volts[start:stop]) ##self.baseline-np.mean(self.voltage.V(start,stop)) works also, as start and stop are int
        ## Anna's request.
        ## was previously measured relative to last spike max. now relative to baseline
        self.adp_10ms=self.baseline-volts[ p1+int(10e-3*int(self.voltage.sampling_rate))]
        self.adp_5ms =self.baseline-volts[ p1+int( 5e-3*int(self.voltage.sampling_rate))]
        self.adp_10ms_t=p1/float(self.voltage.sampling_rate)+10e-3
        self.adp_5ms_t =p1/float(self.voltage.sampling_rate)+5e-3

    @once
    def setup(self):
        self._fig().subplots(1, 1)
        self._cursor(self._axes(0),'h',cfg.AHP_SPIKE_MIN_PEAK,
                    lambda x:cfg.set('AHP_SPIKE_MIN_PEAK',x) or \
                        cfg.set('AHP_SPIKE_MIN_AMP',x-self.parent.cursors[1].getpos()) or
                        self.parent.process(0xFFFF) or \
                        self.parent.draw (False))
        self._cursor(self._axes(0),'h',cfg.AHP_SPIKE_MIN_PEAK-cfg.AHP_SPIKE_MIN_AMP,
                    lambda x:cfg.set('AHP_SPIKE_MIN_AMP',cfg.AHP_SPIKE_MIN_PEAK-x) or \
                        self.parent.process(0xFFFF) or \
                        self.parent.draw (False))
        ## enable manual analysis. When setup is called, process has already been called, therefore
        ## self.peaks and self.ahppos should exist,although they may be nan
        try:
            self.p1=self.peaks['x'][-1]
        except:
            self.p1=0.05
        try:
            self.p2=self.ahp_pos/self.voltage.sampling_rate
            if np.isnan(self.p2):
                self.p2=0.8
        except:
            self.p2=0.8
        self._cursor(self._axes(0),'v',self.p1,
                    lambda x:self.parent.currentframe().__setattr__('p1',x) or \
                        self.manualprocess(0xFFFF) or \
                        self.parent.draw (False))
        self._cursor(self._axes(0),'v',self.p2,
                    lambda x:self.parent.currentframe().__setattr__('p2',x) or \
                        self.manualprocess(0xFFFF) or \
                        self.parent.draw (False))

    def draw(self,drawall=True):
        self.setup() ## ensure that axes are ready!
        self._fig().canvas.TopLevelParent.SetTitle("AHP protocol")
        if drawall:  ## avoid redrawing signals if not required
            self._clf(['traces'])
            self._axes(0).plot(self.voltage.s(), self.voltage.V(),color='blue',gid='traces')
            _autoscale(self._axes(0),self.voltage.s(),self.voltage.V())
        self._clf(['markers'])
        self._axes(0).axhline(self.baseline,color="black",linestyle ="--",gid='markers')
        if not self.ahp_value is None:
            self._axes(0).set_title(f'Calc Freq: {self.frequency:.2f}Hz '+
                               f'AHP : {_pprint(self.ahp_value,pq.V)}')
            self._axes(0).axhline(self.baseline-self.ahp_value,color="green",linestyle ="--",gid='markers')
            self._axes(0).plot(self.ahp_pos/self.voltage.sampling_rate,self.baseline-self.ahp_value,"o",color="green",gid='markers')
        if not (self.ahp_value_1s is None or np.isnan(self.ahp_value_1s)):
            self._axes(0).set_title(f'Calc Freq: {self.frequency:.2f}Hz '+
                               f'AHP : {_pprint(self.ahp_value,pq.V)} '+
                               f'AHP_1s : {_pprint(self.ahp_value_1s,pq.V)}')
            self._axes(0).plot([self.ahp_pos_1s/self.voltage.sampling_rate],[self.baseline-self.ahp_value_1s],"o",color='orange', gid="markers")
        self._axes(0).plot(self.peaks['x'],self.peaks['y'],'x',color='red',gid="markers")
        try:
            if len(self.peaks['x'])!=0:
                self._axes(0).plot(self.adp_5ms_t,self.baseline-self.adp_5ms,'v',color='orange',gid="markers")
                self._axes(0).plot(self.adp_10ms_t,self.baseline-self.adp_10ms,'v',color='orange',gid="markers")
        except:
            pass

class ahpframe(BaseFrame):
    def __init__(self,sig,frequency,apcount,idx,parent):
        self.voltage=sig
        self.sr=int(sig.sampling_rate)
        if not frequency is None:
            self.frequency=frequency
            self.autofreq=False
        else:
            self.frequency=None
            self.autofreq=True
        self.apcount=apcount
        self.ahp_value=None
        self.ahp_value_1s=None
        self.adp_5ms=None
        self.adp_10ms=None
        self.p1=0.1
        self.p2=0.2
        if cfg.AHP_SPIKE_AUTO:
            hi,lo=np.max(self.voltage.V()),np.min(self.voltage.V())
            delta=(hi-lo)
            cfg.AHP_SPIKE_MIN_PEAK=lo+delta*0.5
            cfg.AHP_SPIKE_MIN_AMP=delta*0.35
        super(ahpframe,self).__init__(idx,parent)

    def process(self,bitmask=0xFFFF):
        self.baseline=float(np.mean(self.voltage.V(cfg.AHP_SS_START,cfg.AHP_SS_STOP)))
        volts=self.voltage.V()
        times=self.voltage.s()
        ## working in samples, as we're using find_peaks and argmin
        if cfg.AHP_CHECK_NONE:
            if self.frequency is None or self.apcount is None:
                logging.getLogger().error("cfg.AHP_CHECK_NONE is set but could not parse number of APS or frequency!")
                return
            peak_pos=[int((cfg.AHP_SPIKE_START+n*(1/self.frequency))*int(self.voltage.sampling_rate)) for n in range (self.apcount)]
        else:
            peak_pos,peak_info=scipy.signal.find_peaks(volts, \
                                        height=cfg.AHP_SPIKE_MIN_PEAK,\
                                        prominence=cfg.AHP_SPIKE_MIN_AMP,\
                                        distance=int(0.00040*self.voltage._sampling_rate)) # up to 200Hz
        validcounts=set([cnt for cnt,freq in cfg.AHP_VALID_COMBO])
        validfreqs=set([freq for cnt,freq in cfg.AHP_VALID_COMBO])
        self.peakcount=len(peak_pos)
        self.peaks={'x':times[peak_pos],'y':volts[peak_pos]}
        if self.autofreq:
            try:
                self.frequency=(len(peak_pos)-1)/(times[peak_pos[-1]]-times[peak_pos[0]])
                ## clamp to nearest power of 10
                self.frequency=int(10*round(self.frequency/10))
                ## or get nearest frequency
                idx=np.argmin(np.array(  [abs(f-self.frequency) for f in sorted(validfreqs) ]  ))
                self.frequency=sorted(validfreqs)[idx]
            except:
                self.frequency=np.nan
        if self.peakcount<cfg.AHP_MIN_SPIKE_COUNT:
            logging.getLogger().error("Could not find at least 3 peaks in file!")
            self.ahp_pos=np.nan
            self.ahp_value=np.nan
            self.ahp_pos_1s=np.nan
            self.ahp_value_1s=np.nan
            self.adp_5ms=np.nan
            self.adp_10ms=np.nan
            if self.peakcount<1:
                return
        if cfg.AHP_CHECK_SPIKE_COUNT and not (self.peakcount in validcounts):
            logging.getLogger().error(f"The number of detected peaks ({self.peakcount}) is unexpected!")
            self.ahp_pos=np.nan
            self.ahp_value=np.nan
            self.ahp_pos_1s=np.nan
            self.ahp_value_1s=np.nan
            self.adp_5ms=np.nan
            self.adp_10ms=np.nan
            return
        elif cfg.AHP_CHECK_SPIKE_FREQ and not (self.frequency in validfreqs):
            logging.getLogger().error(f"The computed frequency ({self.frequency}) is unexpected!")
            self.ahp_pos=np.nan
            self.ahp_value=np.nan
            self.ahp_pos_1s=np.nan
            self.ahp_value_1s=np.nan
            self.adp_5ms=np.nan
            self.adp_10ms=np.nan
            return
        ## get the mimimum
        self.ahp_pos=peak_pos[-1]+np.argmin(  volts[peak_pos[-1] : peak_pos[-1] + int(cfg.AHP_MAX_DELAY*self.voltage.sampling_rate) ] )
        #self.ahp_pos=peak_pos[-1]+np.argmin(  volts[peak_pos[-1] : ] )
        start=int(self.ahp_pos-cfg.AHP_TIME_WINDOW_AVERAGE*int(self.voltage.sampling_rate))
        stop=int(self.ahp_pos+cfg.AHP_TIME_WINDOW_AVERAGE*int(self.voltage.sampling_rate))
        self.ahp_value=self.baseline-np.mean(volts[start:stop]) ##self.baseline-np.mean(self.voltage.V(start,stop)) works also, as start and stop are int
        ## Anna's request.
        ## was previously measured relative to last spike max. now relative to baseline
        self.adp_10ms=self.baseline-volts[ peak_pos[-1]+int(10e-3*int(self.voltage.sampling_rate))]
        self.adp_5ms =self.baseline-volts[ peak_pos[-1]+int( 5e-3*int(self.voltage.sampling_rate))]
        self.adp_10ms_t=peak_pos[-1]/float(self.voltage.sampling_rate)+10e-3
        self.adp_5ms_t =peak_pos[-1]/float(self.voltage.sampling_rate)+5e-3
        ## if we succeeded, place vertical cursors accordingly
        ## frames are created before protocol. hence cursors may not be created here
        try:
            self._get_cursor(2).setpos(peak_pos[-1]/self.voltage.sampling_rate)
            self._get_cursor(3).setpos(self.ahp_pos/self.voltage.sampling_rate)
        except:
            pass
        ## get the value 1s after last peak
        try:
            self.ahp_pos_1s=peak_pos[-1]+int(1.0*self.voltage.sampling_rate)
            start=int(self.ahp_pos_1s-cfg.AHP_TIME_WINDOW_AVERAGE*int(self.voltage.sampling_rate))
            stop=int(self.ahp_pos_1s+cfg.AHP_TIME_WINDOW_AVERAGE*int(self.voltage.sampling_rate))
            self.ahp_value_1s=self.baseline-np.mean(volts[start:stop])
        except:
            self.ahp_pos_1s=np.nan
            self.ahp_value_1s=np.nan

    def manualprocess(self,bitmask=0xFFFF):
        ## much easier...
        self.baseline=float(np.mean(self.voltage.V(cfg.AHP_SS_START,cfg.AHP_SS_STOP)))
        volts=self.voltage.V()
        p1=int(self.p1*self.voltage.sampling_rate)
        p2=int(self.p2*self.voltage.sampling_rate)
        self.ahp_pos=p1+np.argmin(volts[p1 : p2 ])
        start=int(self.ahp_pos-cfg.AHP_TIME_WINDOW_AVERAGE*int(self.voltage.sampling_rate))
        stop=int(self.ahp_pos+cfg.AHP_TIME_WINDOW_AVERAGE*int(self.voltage.sampling_rate))
        self.ahp_value=self.baseline-np.mean(volts[start:stop]) ##self.baseline-np.mean(self.voltage.V(start,stop)) works also, as start and stop are int
        ## Anna's request.
        ## was previously measured relative to last spike max. now relative to baseline
        self.adp_10ms=self.baseline-volts[ p1+int(10e-3*int(self.voltage.sampling_rate))]
        self.adp_5ms =self.baseline-volts[ p1+int( 5e-3*int(self.voltage.sampling_rate))]
        self.adp_10ms_t=p1/float(self.voltage.sampling_rate)+10e-3
        self.adp_5ms_t =p1/float(self.voltage.sampling_rate)+5e-3

    @once
    def setup(self):
        self._fig().subplots(1, 1)
        self._cursor(self._axes(0),'h',cfg.AHP_SPIKE_MIN_PEAK,
                    lambda x:cfg.set('AHP_SPIKE_MIN_PEAK',x) or \
                        cfg.set('AHP_SPIKE_MIN_AMP',x-self.parent.cursors[1].getpos()) or
                        self.parent.process(0xFFFF) or \
                        self.parent.draw (False))
        self._cursor(self._axes(0),'h',cfg.AHP_SPIKE_MIN_PEAK-cfg.AHP_SPIKE_MIN_AMP,
                    lambda x:cfg.set('AHP_SPIKE_MIN_AMP',cfg.AHP_SPIKE_MIN_PEAK-x) or \
                        self.parent.process(0xFFFF) or \
                        self.parent.draw (False))
        ## enable manual analysis. When setup is called, process has already been called, therefore
        ## self.peaks and self.ahppos should exist,although they may be nan
        try:
            self.p1=self.peaks['x'][-1]
        except:
            self.p1=0.05
        try:
            self.p2=self.ahp_pos/self.voltage.sampling_rate
            if np.isnan(self.p2):
                self.p2=0.8
        except:
            self.p2=0.8
        self._cursor(self._axes(0),'v',self.p1,
                    lambda x:self.parent.currentframe().__setattr__('p1',x) or \
                        self.manualprocess(0xFFFF) or \
                        self.parent.draw (False))
        self._cursor(self._axes(0),'v',self.p2,
                    lambda x:self.parent.currentframe().__setattr__('p2',x) or \
                        self.manualprocess(0xFFFF) or \
                        self.parent.draw (False))

    def draw(self,drawall=True):
        self.setup() ## ensure that axes are ready!
        self._fig().canvas.TopLevelParent.SetTitle("AHP protocol")
        if drawall:  ## avoid redrawing signals if not required
            self._clf(['traces'])
            self._axes(0).plot(self.voltage.s(), self.voltage.V(),color='blue',gid='traces')
            _autoscale(self._axes(0),self.voltage.s(),self.voltage.V())
        self._clf(['markers'])
        self._axes(0).axhline(self.baseline,color="black",linestyle ="--",gid='markers')
        if not self.ahp_value is None:
            self._axes(0).set_title(f'Calc Freq: {self.frequency:.2f}Hz '+
                               f'AHP : {_pprint(self.ahp_value,pq.V)}')
            self._axes(0).axhline(self.baseline-self.ahp_value,color="green",linestyle ="--",gid='markers')
            self._axes(0).plot(self.ahp_pos/self.voltage.sampling_rate,self.baseline-self.ahp_value,"o",color="green",gid='markers')
        if not (self.ahp_value_1s is None or np.isnan(self.ahp_value_1s)):
            self._axes(0).set_title(f'Calc Freq: {self.frequency:.2f}Hz '+
                               f'AHP : {_pprint(self.ahp_value,pq.V)} '+
                               f'AHP_1s : {_pprint(self.ahp_value_1s,pq.V)}')
            self._axes(0).plot([self.ahp_pos_1s/self.voltage.sampling_rate],[self.baseline-self.ahp_value_1s],"o",color='orange', gid="markers")
        try:
            self._axes(0).plot(self.peaks['x'],self.peaks['y'],'x',color='red',gid="markers")
        except:
            pass
        try:
            if len(self.peaks['x'])!=0:
                self._axes(0).plot(self.adp_5ms_t,self.baseline-self.adp_5ms,'v',color='orange',gid="markers")
                self._axes(0).plot(self.adp_10ms_t,self.baseline-self.adp_10ms,'v',color='orange',gid="markers")
        except:
            pass


class ahpprotocol(BaseProtocol):
    def __init__(self,sigs,interactive,frequency=None,apcount=None):
        if cfg.AHP_SIMPLIFIED_PROTOCOL and (apcount,frequency) in cfg.AHP_VALID_COMBO:
            self.frames=[ahpsimpleframe(s,frequency,apcount,idx=e,parent=self) for e,s in enumerate(sigs) ]
        else:
            self.frames=[ahpframe(s,frequency,apcount,idx=e,parent=self) for e,s in enumerate(sigs) ]
        super(ahpprotocol,self).__init__(interactive)
    def provides(self):
        r={}
        for cnt,freq in cfg.AHP_VALID_COMBO:
            if cnt<6:
                r.update({f'AHP_{cnt}_{freq}Hz_min':'maximal hyperpolarization after last detected pulse.'})
            if cnt>6:
                r.update({f'AHP_{cnt}_{freq}Hz_min':'maximal hyperpolarization after last detected pulse.'})
                r.update({f'AHP_{cnt}_{freq}Hz_1s':'hyperpolarization 1s after last detected pulse.'})
        for cnt,freq in cfg.AHP_VALID_COMBO:
            r.update({f'AHP_{cnt}_{freq}Hz_adp_5ms':"ADP 5 ms after last spike (voltage(peak) -voltage(peak+5)"})
            r.update({f'AHP_{cnt}_{freq}Hz_adp_10ms':"ADP 10 ms after last spike (voltage(peak) -voltage(peak+5)"})
        return r
    def results(self):
        sign=-1 if cfg.AHP_CORRECT_SIGNS else 1
        cnt=self.frames[0].peakcount
        freq=self.frames[0].frequency
        if cnt<6: ## AHP MED protocol
            self.r= {f'AHP_{cnt}_{freq}Hz_min':sign*self.frames[0].ahp_value/cfg.OUTPUT_V_SCALE}
        elif cnt>5: ## AHP SLOW protocol
            self.r= {f'AHP_{cnt}_{freq}Hz_min':sign*self.frames[0].ahp_value/cfg.OUTPUT_V_SCALE,
                    f'AHP_{cnt}_{freq}Hz_1s':sign*self.frames[0].ahp_value_1s/cfg.OUTPUT_V_SCALE}
        self.r.update({f'AHP_{cnt}_{freq}Hz_adp_5ms':sign*self.frames[0].adp_5ms/cfg.OUTPUT_V_SCALE})
        self.r.update({f'AHP_{cnt}_{freq}Hz_adp_10ms':sign*self.frames[0].adp_10ms/cfg.OUTPUT_V_SCALE})
        return self.r

'''
    IV protocol,
    counts spikes, measures spike properties, AHP, resistance,...
    input:  sigs: array of neo.io.AnalogSignal with units V, mV (units are not checked)

    cfg: lots...
    usage: protocol=ivprotocol(sig,interactive)
           print(protocol.results())
'''
class spike(object):
    def __init__(self,signal,pos,idx,fidx,ahpbaseline=None):
        pre=cfg.IV_SPIKE_PRE_TIME
        post=cfg.IV_SPIKE_POST_TIME
        prepts=cfg.IV_SPIKE_PRE_TIME*signal._sampling_rate          ## number of points to keep before peak
        postpts=cfg.IV_SPIKE_POST_TIME*signal._sampling_rate        ## number of points to keep after peak
        volts=signal.V()                                        ## convert to raw numpy array
        times=signal.s()                                        ## convert to raw numpy array
        self.pos=pos                                            ## pos of spike (in samples)in frame
        self.idx=idx                                            ## the index of spike in frame
        self.fidx=fidx                                          ## the frame the spike belongs to belongs to
        self.time=times[pos]                                    ## time of spike in frame
        self.peak=volts[pos]                                    ## peak amplitude of spike
        self.ISI=np.nan                                         ## inter spike interval. will be calculated later
        self.evoked=False                                       ## spike is evoked spike. will be calculated later
        self.rebound=False                                      ## spike is rebound spike
        ## position and value for max rising slope (in samples)
        self.maxrisepos=np.argmax(np.gradient(   signal.V(self.time-pre,self.time+post)   ))
        self.maxrise=float(np.max(np.gradient(   signal.V(self.time-pre,self.time+post)   )) * signal._sampling_rate) ## to convert to V/s
        self.maxrisepos+=self.pos-int(pre*signal._sampling_rate)

        ## position and value for max descending slope (in samples)
        self.maxfallpos=np.argmin(np.gradient(  signal.V(self.time-pre,self.time+post)   ))
        self.maxfall=float(np.min(np.gradient(  signal.V(self.time-pre,self.time+post)   )) *signal._sampling_rate)
        self.maxfallpos+=self.pos-int(pre*signal._sampling_rate)

        ## phase plane values. As it is guaranteed that they will exist, we have to write them before trying to find threshold
        ## for phase plane analysis, we'll keed a list of voltages and voltage variation
        #self.PPV=volts[pos-int(prepts):pos+int(postpts)]
        self.PPV=signal.V(self.time-pre,self.time+post)
        self.PPdV=np.gradient(self.PPV)* signal._sampling_rate ## to convert to V/s

        ## position and value for threshold
        ## using second derivarive maximum is very unefficient.
        ## using second derivative threshold isn't more efficient than maximum.
        ## see https://stackoverflow.com/questions/3843017/efficiently-detect-sign-changes-in-python
        ## the latest algorithm is as follow: get the threshold pos both on first and second derivatives, and take the first one!
        try:
            thrsignal=np.gradient(np.gradient(  signal.V(self.time-pre,self.time+post)  )) -float(cfg.IV_SPIKE_DV_THRESHOLD)
            self.thresholdpos1=np.where(np.diff(np.signbit(thrsignal)))[0][0]
            self.thresholdpos1+=self.pos-int(pre*signal._sampling_rate)
        except:
            self.thresholdpos1=np.nan
        try:
            thrsignal=np.gradient(             signal.V(self.time-pre,self.time+post) ) -float(cfg.IV_SPIKE_DV_THRESHOLD)
            self.thresholdpos2=np.where(np.diff(np.signbit(thrsignal)))[0][0]
            self.thresholdpos2+=self.pos-int(pre*signal._sampling_rate)
        except:
            self.thresholdpos2=np.nan
        if cfg.IV_SPIKE_LOWEST_THRESHOLD:
            self.thresholdpos=np.nanmin([self.thresholdpos1,self.thresholdpos2])
        else:
            self.thresholdpos=self.thresholdpos1 if self.thresholdpos1!=np.nan else self.thresholdpos2

        ## if we failed at identifying a threshold, then mark spike as incomplete and use np.nan values for the remaining spike measurements
        if np.isnan(self.thresholdpos) :
            logging.getLogger(__name__).warning(f"Could not isolate threshold for spike {self.idx} in frame {self.fidx}")
            self.complete=False
            self.thresholdpos=np.nan
            self.threshold=np.nan
            self.amplitude=np.nan
            self.halfwidth=np.nan
            self.hwpos=[np.nan,np.nan]
            #self.ahp=None ## will be overriden in frame analysis
            return
        else:
            self.complete=True
            self.thresholdpos=int(self.thresholdpos)
            self.threshold=volts[self.thresholdpos]
            self.amplitude=self.peak-self.threshold
            ## position and value for half width 
            ## could be more precise here: we could find the exact time at which the signal crosses zero (),
            ## instead of first point before a zero crossing event occurs
            self.halfvoltage=self.peak-(self.peak-self.threshold)/2
            hwsignal=signal.V(self.time-pre,self.time+post)-self.halfvoltage
            self.hwpos=np.where(np.diff(np.signbit(hwsignal)))[0]
            self.hwpos[0]+=self.pos-int(pre*signal._sampling_rate)
            try:
                ## for weird spikes, it may happen thta voltage does not fall back to half voltage...
                self.hwpos[1]+=self.pos-int(pre*signal._sampling_rate)
                self.halfwidth=float((self.hwpos[1]-self.hwpos[0])/signal._sampling_rate)
            except:
                self.hwpos=np.append(self.hwpos,np.nan)
                self.halfwidth=np.nan
                self.complete=False

class ivframe(BaseFrame):
    bitmask_ALL=0xFFFF          ## reprocess time constant
    bitmask_TC =1<<0            ## reprocess time constant
    bitmask_SPIKES =1<<1        ## reprocess time constant
    def __init__(self,sig,idx,parent,current=None):
        self.voltage=sig
        self.sr=int(sig.sampling_rate)
        self.idx=idx
        if current==None:
            self.current=cfg.IV_CURRENT_STEPS[self.idx]
        else:
            self.current=current
        ## membrane time constant fit:
        ## each frame keeps its own settings
        self.fitter=None
        self.fitstart=cfg.IV_TCFIT_START
        self.fitstop=-1 if cfg.IV_TCFIT_AUTOSTOP else cfg.IV_TCFIT_STOP
        ## no spike for now
        self.spikes=[]
        super(ivframe,self).__init__(idx,parent)

    def process(self,bitmask=0xFFFF):
        ## baseline,resistance, sagratio
        self.baseline=np.mean(self.voltage.V(cfg.IV_BASELINE_START,cfg.IV_BASELINE_STOP))
        self.sagpeak=np.min(self.voltage.V(cfg.IV_SAG_PEAK_START,cfg.IV_SAG_PEAK_STOP))
        self.sagss=np.mean(self.voltage.V(cfg.IV_SAG_SS_START,cfg.IV_SAG_SS_STOP))
        self.sagratio=(self.baseline-self.sagss)/(self.baseline-self.sagpeak) if self.current<0 else None
        self.sagratio_pct=(self.sagss-self.sagpeak)/(self.baseline-self.sagss)*100 if self.current<0 else None
        self.resistance=(self.baseline-self.sagpeak)/self.current*1e12 if self.current!=0 else None
        self.resistance_interp=np.nan

        ##other analyses are in separated funcs
        if bitmask & ivframe.bitmask_TC and self.current<=cfg.IV_TCFIT_THRESHOLD:
            self.process_tc()
        if bitmask & ivframe.bitmask_SPIKES:
            self.process_spikes()
            self.process_firingpattern()
            self.process_sfa()

    def process_tc(self):
        ##if required, try to determine the end of fitting region
        if self.fitstop==-1:
            ## find minimal value
            self.fitstop=float(np.argmin(self.voltage.V(cfg.IV_CURRENT_INJECTION_START,cfg.IV_CURRENT_INJECTION_STOP))/float(self.voltage.sampling_rate)+cfg.IV_CURRENT_INJECTION_START)
            ## adjust minimal value
            self.fitstop=cfg.IV_CURRENT_INJECTION_START+(self.fitstop-cfg.IV_CURRENT_INJECTION_START)*0.8
            self.fitstop=float(np.min([self.fitstop,cfg.IV_CURRENT_INJECTION_START+(cfg.IV_TCFIT_STOP-cfg.IV_TCFIT_START)*1.2])) ##initially 1.2; 0.8 would be better?
        times=self.voltage.s(self.fitstart,self.fitstop)
        volts=self.voltage.V(self.fitstart,self.fitstop)
        self.fitter=XYFitter(times,volts,cfg.IV_TCFIT_ORDER,cfg.IV_TCFIT_WEIGHTED_AVERAGE,self.fitstart,
                            maxfev=cfg.ITSQ_FIT_ITERATION_COUNT,
                            version=cfg.ITSQ_FITTER_VERSION)
        ## computed fitted curve till the end of current pulse
        if self.fitter.success:
            self.fitline=[               self.voltage.s(cfg.IV_CURRENT_INJECTION_START,cfg.IV_CURRENT_INJECTION_STOP),
                        self.fitter.line(self.voltage.s(cfg.IV_CURRENT_INJECTION_START,cfg.IV_CURRENT_INJECTION_STOP))]
            self.resistance_interp=(self.fitline[1][-1]-self.baseline)/self.current*1e12 if self.current!=0 else None
        
    def process_spikes(self):
        ## convenient variables to simplify writing...
        times=self.voltage.s()
        volts=self.voltage.V()
        sr=int(self.voltage.sampling_rate)
        ## detect peaks
        peak_pos,peak_infos=scipy.signal.find_peaks(volts, \
                                    height=cfg.IV_SPIKE_MIN_PEAK,\
                                    prominence=cfg.IV_SPIKE_MIN_AMP,\
                                    #width=(int(0.0001*sr),int(0.05*sr)),\
                                    distance=int(cfg.IV_SPIKE_MIN_INTER*sr),\
                                    )

        ## make sure we do not have a spike at the beginning or at the end of frame (in which case we could not take pre and post points)
        skipstart=cfg.IV_SPIKE_PRE_TIME*sr
        skipend=len(self.voltage)-cfg.IV_SPIKE_POST_TIME*sr
        peak_pos=[p for p in peak_pos if p>skipstart and p<skipend]
        ## try to determine baseline
        self.ahpbaseline=self._try_guess_ahp_baseline(peak_pos)
        ## build the list of spikes
        if cfg.ITSQ_ENABLE_MULTIPROCESSING and len(peak_pos)>100:
            from multiprocessing import Pool
            with Pool() as pool:
                star_peak_pos=[(self.voltage,p,e,self.idx,self.ahpbaseline)   for e,p in enumerate(peak_pos) ]
                self.spikes=pool.starmap(spike,star_peak_pos,)
        else:
            self.spikes=[  spike(self.voltage,p,e,self.idx,self.ahpbaseline)   for e,p in enumerate(peak_pos) ]
        ## make list of evoked and rebound spikes and save attribute in spike object
        self.reboundspikes=[s for s in self.spikes if s.time>cfg.IV_CURRENT_INJECTION_STOP and self.current<0]
        self.evokedspikes=[s for s in self.spikes if cfg.IV_CURRENT_INJECTION_START<s.time<cfg.IV_CURRENT_INJECTION_STOP and self.current>=cfg.IV_SPIKE_EVOKED_THRESHOLD]
        for s in self.reboundspikes:
            s.rebound=True
        for s in self.evokedspikes:
            s.evoked=True
        ## calculate interspike interval
        for e,s in enumerate(self.evokedspikes):
            s.ISI=s.time-cfg.IV_CURRENT_INJECTION_START if e==0 else s.time-self.evokedspikes[e-1].time
        ## for evoked spikes, extract minimum following spike, aka ahp
        ahp_spikes=[s for s in self.evokedspikes if s.complete]
        for e,s in enumerate([s for s in self.evokedspikes]):
            if e<(len(self.evokedspikes)-1): ## we are sure that there will be another spike after
                s.ahppos=s.pos+np.argmin(   self.voltage.V(s.time,min(s.time+0.05,self.evokedspikes[e+1].time))  ) ## this line crashes
                s.ahp=volts[s.ahppos]####YLF26APRIL#### self.ahpbaseline-volts[s.ahppos]
            else:
                s.ahppos=s.pos+np.argmin(   self.voltage.V(s.time,min(s.time+0.05,cfg.IV_CURRENT_INJECTION_STOP))    )
                s.ahp=volts[s.ahppos]####YLF26APRIL#### self.ahpbaseline-volts[s.ahppos]
        ## end of spikes processing. store meta information for drawing
        self.meta={}
        self.meta['maxriseV']=   {'x': times[[s.maxrisepos for s in self.spikes]],\
                                  'y':volts[[s.maxrisepos for s in self.spikes]] }
        self.meta['maxrisedV']=  {'x': times[[s.maxrisepos for s in self.spikes]],\
                                  'y':[s.maxrise for s in self.spikes] }
        self.meta['maxfallV']=   {'x': times[[s.maxfallpos for s in self.spikes]],\
                                  'y':volts[[s.maxfallpos for s in self.spikes]] }
        self.meta['peak']=       {'x':[s.time for s in self.spikes],\
                                  'y':[s.peak for s in self.spikes] }
        self.meta['threshold']=  {'x':times[[s.thresholdpos for s in self.spikes if s.complete]],\
                                  'y':[s.threshold for s in self.spikes  if s.complete]}
        self.meta['hwstart']=    {'x':times[[s.hwpos[0] for s in self.spikes  if s.complete]],\
                                  'y':volts[[s.hwpos[1] for s in self.spikes  if s.complete]]}
        self.meta['hwstop']=     {'x':times[[s.hwpos[1] for s in self.spikes  if s.complete]], \
                                  'y':volts[[s.hwpos[1] for s in self.spikes  if s.complete]]}
        self.meta['ahp']=        {'x':times[[s.ahppos for s in self.evokedspikes  if s.complete]],\
                                  #'y':[self.ahpbaseline-s.ahp for s in self.evokedspikes  if s.complete]}
                                  'y':[s.ahp for s in self.evokedspikes  if s.complete]}
    
    def _try_guess_ahp_baseline(self,pp):
            sr=int(self.voltage.sampling_rate)
            basesignal=self.voltage.V()
            basesignal[0:int(cfg.IV_CURRENT_INJECTION_START*sr)]=np.nan
            basesignal[int(cfg.IV_CURRENT_INJECTION_STOP*sr):]=np.nan
            for p in pp:
                basesignal[p-int(cfg.IV_SPIKE_PRE_TIME*sr):p+int(cfg.IV_SPIKE_POST_TIME*sr)]=np.nan
            return np.nanmean(basesignal)

    def process_firingpattern(self):
        '''pattern classification according to candelas et al.
        https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3424761/ (Tadros, 2012)
        https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1665382/ (graham, 2004)
        Single spike     : less than 2 AP/pulse - and both AP within the first 250ms
        Delayed          : first latency>95 ms and spiking frequency>8Hz within the  first 5 spikes
        Transient        : last spike time<1.4s - and number of spikes>3. 1.4 s seems very late to me (say 1s)
        Gap firing       : latency>95ms and avg frequency(1-8)<8Hz
        Regular tonic    : tonic and SEM ap frequency (1-4)<2
        Irregular tonic  : tonic and SEM ap frequency (1-4)>2
        Gap firing       : latency>95ms and avg frequency(1-8)<8Hz
        the above classification fails when there is an isolated spike in the middle of the frame
        I just added a special case to classify these cells as "delayed"
        '''
        def freq(spikes):
            return (len(spikes)-1)/(spikes[-1].time-spikes[0].time)
        def sem(spikes):
            return scipy.stats.sem(np.diff([s.time for s in spikes]))

        self.pattern="Undetermined"
        if self.current<=0:
           self.pattern=None
        if len([s for s in self.evokedspikes])==0:
            self.pattern=="silent" ## obviously!
        elif len([s for s in self.evokedspikes])<=2 and max([s.time-cfg.IV_CURRENT_INJECTION_START for s in self.evokedspikes])<0.125:
            self.pattern=p="single" ## strange that doublet spiking are indeed considered as single spiking
        elif len([s for s in self.evokedspikes])>=5 and min([s.time-cfg.IV_CURRENT_INJECTION_START for s in self.evokedspikes])>0.1:
            self.pattern=="delayed"## 
        elif len([s for s in self.evokedspikes])>=3 and max([s.time-cfg.IV_CURRENT_INJECTION_START for s in self.evokedspikes])<1.0:
            self.pattern="transient"
        elif len([s for s in self.evokedspikes])>=3 and min([s.time-cfg.IV_CURRENT_INJECTION_START for s in self.evokedspikes])>0.095 and freq(self.evokedspikes[:8])<8.0:
            self.pattern="gap"
        elif len([s for s in self.evokedspikes])>=3 and sem(self.evokedspikes[:4])>2:
            self.pattern="tonic_irregular"
        elif len([s for s in self.evokedspikes])>=3 and sem(self.evokedspikes[:4])<2:
            self.pattern="tonic"

    def process_sfa(self):
        if len(self.evokedspikes)<cfg.IV_MIN_SPIKES_FOR_SFADAPT:
            self.sfa_freq_lin=None
            self.sfa_freq_log=None
            self.sfa_freq_div=None
            self.sfa_peak_lin=None
            self.sfa_peak_log=None
            self.sfa_peak_div=None
            self.fano=None
        else:
            ## for intervals
            y=[s.ISI for s in self.evokedspikes[1:] ]
            x=list(range(len(y)))
            self.sfa_freq_lin, self.freq_intercept_lin, r_value_lin, p_value_lin, std_err_lin = scipy.stats.linregress(x,y)
            self.sfa_freq_log, self.freq_intercept_log, r_value_log, p_value_log, std_err_log = scipy.stats.linregress(x,np.log(y))
            self.sfa_freq_div =self.evokedspikes[-1].ISI/self.evokedspikes[1].ISI
            self.fano=np.std(y)/np.mean(y)
            ## for peaks
            y=[s.peak for s in self.evokedspikes[1:] ]
            x=list(range(len(y)))
            self.sfa_peak_lin, self.peak_intercept_lin, r_value_lin, p_value_lin, std_err_lin = scipy.stats.linregress(x,y)
            self.sfa_peak_log, self.peak_intercept_log, r_value_log, p_value_log, std_err_log = scipy.stats.linregress(x,np.log(y))
            self.sfa_peak_div =self.evokedspikes[-1].peak/self.evokedspikes[1].peak

    def activate(self):
        self._get_cursor(0).setpos(self.fitstart)
        self._get_cursor(1).setpos(self.fitstop)

    def charts(self,*args,**kwargs):
        fig,ax=plt.subplots(2,3)
        a00,a01,a02,a10,a11,a12=ax[0][0],ax[0][1],ax[0][2],ax[1][0],ax[1][1],ax[1][2]
        a00.plot(self.spikes[0].PPV,self.spikes[0].PPdV)
        for s in self.spikes[1:]:
            a00.plot(s.PPV,s.PPdV,color='orange')
        a00.plot(np.mean(np.array([s.PPV for s in self.spikes]),axis=0),
                np.mean(np.array([s.PPdV for s in self.spikes]),axis=0) )
        a00.set(xlabel='Voltage (V)',ylabel='dV (V)',title='Phase plane')
        if len(self.evokedspikes)>=cfg.IV_MIN_SPIKES_FOR_SFADAPT:
            y=[s.ISI for s in self.evokedspikes[1:] ]
            x=list(range(len(y)))
            a01.plot(x, y,"o")
            a01.plot(x, [s*self.sfa_freq_lin+self.freq_intercept_lin for s in x])
            a01.set(xlabel='Spike index',ylabel='Interval',title='Spike Freq delay (lin)')
            a11.plot(x, np.log(y),"o")
            a11.plot(x, [s*self.sfa_freq_log+self.freq_intercept_log for s in x])
            a11.set(xlabel='Spike index',ylabel='Interval',title='Spike Freq delay (log)')
            y=[s.peak for s in self.evokedspikes[1:] ]
            a02.plot(x, y,"o")
            a02.plot(x, [s*self.sfa_peak_lin+self.peak_intercept_lin for s in x])
            a02.set(xlabel='Spike index',ylabel='Peak',title='Spike Freq peak (lin)')
            a12.plot(x, np.log(y),"o")
            a12.plot(x, [s*self.sfa_peak_log+self.peak_intercept_log for s in x])
            a12.set(xlabel='Spike index',ylabel='Peak',title='Spike Freq peak (log)')
        fig.tight_layout()
        fig.show()

    @once
    def setup(self):
        self._fig().subplots(2, 1, gridspec_kw={'height_ratios': [3, 1],"top":0.9},sharex = True)
        testbtn=TriggerBtn(self._fig(),"charts",'alt+c',str(Path(__file__).parent/'resources/fa-linechart-solid.png'),'Chart graphics',
                    lambda *args,**kwargs:self.parent.currentframe().charts(*args,**kwargs))
        self._cursor(self._axes(),'v',self.fitstart,
                    lambda x:self.parent.currentframe().__setattr__('fitstart',x) or \
                        self.parent.process(ivframe.bitmask_TC) or \
                        self.parent.draw (False)
                    )
        self._cursor(self._axes(),'v',self.fitstop,
                    lambda x:self.parent.currentframe().__setattr__('fitstop',x) or \
                        self.parent.process(ivframe.bitmask_TC) or \
                        self.parent.draw (False)
                    )
        self._cursor(self._axes(0),'h',cfg.IV_SPIKE_MIN_PEAK,
                    lambda x:cfg.set('IV_SPIKE_MIN_PEAK',x) or \
                        cfg.set('IV_SPIKE_MIN_AMP',x-self.parent.cursors[3].getpos()) or
                        self.parent.process(ivframe.bitmask_SPIKES) or \
                        self.parent.draw (False)
                    )
        self._cursor(self._axes(0),'h',cfg.IV_SPIKE_MIN_PEAK-cfg.IV_SPIKE_MIN_AMP,
                    lambda x:cfg.set('IV_SPIKE_MIN_AMP',cfg.IV_SPIKE_MIN_PEAK-x) or \
                        self.parent.process(ivframe.bitmask_SPIKES) or \
                        self.parent.draw (False)
                    )
        self._cursor(self._axes(1),'h',cfg.IV_SPIKE_DV_THRESHOLD,
                    lambda x:cfg.set('IV_SPIKE_DV_THRESHOLD',x) or self.parent.process(ivframe.bitmask_SPIKES) or self.parent.draw (False)
                    )

    def draw(self,drawall=True):
        self.setup() ## ensure that axes are ready!
        self._fig().canvas.TopLevelParent.SetTitle(f"IV/Spontaneous firing protocol {self.current}pA")
        title=''
        if drawall:  ## avoid redrawing signals if not required
            self._clf(['traces'])
            aa=len(self.voltage)<200e3
            self._axes(0).plot(self.voltage.s(), self.voltage.V(),color='blue', gid='traces',aa=aa, linewidth=1)
            self._axes(1).plot(self.voltage.s(),np.gradient(self.voltage.V()), color='green',gid='traces',aa=aa,linewidth=1)
            self._axes(1).plot(self.voltage.s(),np.gradient(np.gradient(self.voltage.V())), color='orange',gid='traces',aa=aa,linewidth=1)
            _autoscale(self._axes(0),self.voltage.s(),self.voltage.V())
        self._clf(['markers'])
        self._axes(0).axhline(self.baseline,color="grey",linestyle ="--",gid='markers')
        if self.current<0: ## for negative current, plot sagss and sagpeak
            title+=f'sagratio: {self.sagratio:.2f} '
            self._axes(0).axhline(self.sagss,color="blue",linestyle ="--",gid='markers')
            self._axes(0).axhline(self.sagpeak,color="orange",linestyle ="--",gid='markers')
        if self.fitter and self.fitter.success and self.current<=cfg.IV_TCFIT_THRESHOLD: ##plot fitter if fitting was successful  (or if fitter esists)
            title+=f'TC: {_pprint(self.fitter.tc,pq.s)} '
            self._axes(0).plot( self.fitline[0], self.fitline[1],color='red',gid='markers')
        ## plot spike keypoints
        self._axes(0).plot(self.meta['peak']['x'],self.meta['peak']['y'],"x",color="red",gid="markers")
        self._axes(0).plot(self.meta['maxriseV']['x'],self.meta['maxriseV']['y'],"o",color="orange",gid="markers")
        self._axes(0).plot(self.meta['threshold']['x'],self.meta['threshold']['y'],"+",color="red",gid="markers")
        self._axes(0).plot(self.meta['hwstart']['x'],self.meta['hwstart']['y'],"3",color="red",gid="markers")
        self._axes(0).plot(self.meta['hwstop']['x'],self.meta['hwstop']['y'],"4",color="red",gid="markers")
        self._axes(0).plot(self.meta['ahp']['x'],self.meta['ahp']['y'],"+",color="purple",gid="markers")
        self._axes(0).set_title(title)
        ## beta feature. Not a major improvement, even with  numba and custom caching + generates errors
        ## nb np_cache is incredibly slow
        #_axes(0).callbacks.connect('xlim_changed', self.fastplt)

'''
    def fastplt(self,*ax):
        ##fastplt should round to nearest sec, and resample only if signal has changed
        xlo,xhi=self._axes(0).get_xlim()
        ## clamp xlo and xhi
        xlo=_clamp(int(xlo*self.voltage.sampling_rate),0, len(self.voltage))
        xhi=_clamp(int(xhi*self.voltage.sampling_rate),0, len(self.voltage))
        sig=self.voltage[xlo:xhi]
        x,y=min_max_downsample_v4(sig.V(),sig.s(),4*2500)
        self._axes(0).lines[0].set_data(x,y)
        self._axes(1).lines[0].set_data(x,np.gradient(y))
        self._axes(1).lines[1].set_data(x,np.gradient(np.gradient(y)))

    def fastpltcache(self,*ax):
        ##alternative version
        if not hasattr(self,'mipmaps'):
            self.mipmaps={len(self.voltage):(self.voltage.V(),self.voltage.s())}
        xlo,xhi=self._axes(0).get_xlim()
        npoints=(xhi-xlo)*int(self.voltage.sampling_rate)
        rf=npoints//1680 ## assume 1680 width screen. should get real ex pixel span)
        from math import ceil, log
        ## the trick here is to use discrete resampling levels, so they can be cached by numpy
        rf=10**(ceil(log(rf,10)))
        npts= len(self.voltage)//rf
        ## clamp xlo and xhi
        xlo=_clamp(int(xlo*self.voltage.sampling_rate),0, len(self.voltage))
        xhi=_clamp(int(xhi*self.voltage.sampling_rate),0, len(self.voltage))
        npts=_clamp(npts,1,len(self.voltage))
        try:
            print(f"Using saved mipmaps for level {npts}")
            x,y=self.mipmaps[npts]
        except:
            print(f"Computing mipmaps for level {npts}")
            x,y=min_max_downsample_v4(self.voltage.V(),self.voltage.s(),npts)
            self.mipmaps[npts]=(x,y)
        self._axes(0).lines[0].set_data(x,y)
        #_axes(1).lines[0].set_data(x,np.gradient(y))
        #_axes(1).lines[1].set_data(x,np.gradient(np.gradient(y)))
        
from numba import jit, prange
@jit(parallel=True)
def min_max_downsample_v4(x,y, num_bins):
        pts_per_bin = x.size // num_bins
        x_view = x[:pts_per_bin*num_bins].reshape(num_bins, pts_per_bin)
        y_view = y[:pts_per_bin*num_bins].reshape(num_bins, pts_per_bin)    
        i_min = np.zeros(num_bins,dtype='int64')
        i_max = np.zeros(num_bins,dtype='int64')

        for r in prange(num_bins):
            min_val = y_view[r,0]
            max_val = y_view[r,0]
            for c in range(pts_per_bin):
                if y_view[r,c] < min_val:
                    min_val = y_view[r,c]
                    i_min[r] = c
                elif y_view[r,c] > max_val:
                    max_val = y_view[r,c]
                    i_max[r] = c                
        r_index = np.repeat(np.arange(num_bins), 2)
        c_index = np.sort(np.stack((i_min, i_max), axis=1)).ravel()        
        return x_view[r_index, c_index], y_view[r_index, c_index]
'''
class ivprotocol(BaseProtocol):
    def __init__(self,sigs,interactive):
        self.frames=[ivframe(s,idx=e,parent=self) for e,s in enumerate(sigs) ]
        super(ivprotocol,self).__init__(interactive)
    def provides(self):
        r={'IV_baseline':'average baseline (all frames).',
                'IV_resistance':'average resistance (frames with sag_ratio>0.95).',
                'IV_resistance_interp':'interpolated resistance (calculated from fit).',
                'IV_tc':'average time constant (frames with injected current<IV_TCFIT_THRESHOLD).',
                f'IV_sagratio_I={cfg.IV_SAG_TARGET_CURRENT}pA':'sag ratio (base-ss)/(base-peak) for IV_SAGRATIO_TGT_CURRENT amplitude.',
                f'IV_sagratio_I={cfg.IV_SAG_TARGET_CURRENT}pA_pct':'(ss-peak)/(base-ss)*100 for for IV_SAGRATIO_TGT_CURRENT amplitude.',
                f'IV_sagratio_tgt={cfg.IV_SAG_SS_TARGET_VOLTAGE}V':'sag ratio (base-ss)/(base-peak) for frame with baseline-steadystate closest to IV_SAGRATIO_TGT_VOLTAGE.',
                f'IV_sagratio_tgt={cfg.IV_SAG_SS_TARGET_VOLTAGE}V_pct':'(ss-peak)/(base-ss)*100 for frame with baseline-steadystate closest to IV_SAGRATIO_TGT_VOLTAGE.',
                'IV_rheobase':'current required to observe a spike between cfg.IV_CURRENT_INJECTION_START and cfg.IV_CURRENT_INJECTION_STOP.',
                'IV_avg_spike_threshold':'spike threshold. average computed on first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_avg_spike_peak':'spike peak. averagecomputed on first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_avg_spike_amplitude':'spike amplitude (=peak-threshold). averagecomputed on first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_avg_spike_half_width':'spike half width (at (peak-threshold)/2). averagecomputed on first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_avg_spike_max_rise_slope':'spike maximum rise slope. averagecomputed on first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_avg_spike_max_fall_slope':'spike maximum fall slope. averagecomputed on first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_avg_spike_ahp':'spike ahp. average computed on first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_avg_spike_thr2ahp':'difference between threshold and ahp (aka fast_ahp). averagecomputed on first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_first_spike_threshold':'spike threshold. computed on first spike of first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_first_spike_peak':'spike peak. computed on first spike of first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_first_spike_amplitude':'spike amplitude (=peak-threshold). computed on first spike of first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_first_spike_half_width':'spike half width (at (peak-threshold)/2). computed on first spike of first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_first_spike_max_rise_slope':'spike maximum rise slope. computed on first spike of first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_first_spike_max_fall_slope':'spike maximum fall slope. computed on first spike of first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_first_spike_ahp':'spike ahp. computed on first spike of first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_first_spike_thr2ahp':'difference between threshold and ahp (aka fast_ahp). computed on first spike of first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_first_spike_delay':'delay of first spike. computed on first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_first_spike_interval':'interspike interval for two first spikes. computed on first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_last_spike_interval':'interspike interval for two last spikes. computed on first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_first_div_last_spike_interval':'ratio between first and last spike intervals. computed on first frame with more than cfg.IV_MIN_SPIKES_FOR_MEASURE spikes.',
                'IV_sfa_freq_lin':'spike frequency adaptation of spike intervals - linear fit. computed on frame with the more spikes if number of spikes > cfg.IV_MIN_SPIKES_FOR_SFADAPT.',
                'IV_sfa_freq_log':'spike frequency adaptation of spike intervals - log fit. computed on frame with the more spikes if number of spikes > cfg.IV_MIN_SPIKES_FOR_SFADAPT.',
                'IV_sfa_freq_div':'spike frequency adaptation of spike intervals - quotient. computed on frame with the more spikes if number of spikes > cfg.IV_MIN_SPIKES_FOR_SFADAPT.',
                'IV_sfa_peak_lin':'spike frequency adaptation of spike peak - linear fit. computed on frame with the more spikes if number of spikes > cfg.IV_MIN_SPIKES_FOR_SFADAPT.',
                'IV_sfa_peak_log':'spike frequency adaptation of spike peak - log fit. computed on frame with the more spikes if number of spikes > cfg.IV_MIN_SPIKES_FOR_SFADAPT.',
                'IV_sfa_peak_div':'spike frequency adaptation of spike peak - quotient. computed on frame with the more spikes if number of spikes > cfg.IV_MIN_SPIKES_FOR_SFADAPT.',
                'IV_half_width_ratio_3/1':'ratio of half 3rd and first ap half width',
                #'IV_third_spike_threshold':'third spike threshold (if present)',
                #'IV_third_spike_peak':'third spike peak (if present)',
                #'IV_third_spike_amplitude':'third spike amplitude (if present)',
                'IV_third_spike_half_width':'third spike half width (if present)',
                #'IV_third_spike_max_rise_slope':'third spike maximum rise slope (if present)',
                #'IV_third_spike_max_fall_slope':'third spike maximum fall slope (if present)',
                'IV_max_nb_spikes':'maximal number of spikes evoked',
                'IV_max_freq':'maximal firing frequency',
                'IV_firing_pattern':'spike firing pattern. buggy and meaningless',
                'IV_fano':'fano factor. computed on frames with the more spikes',
                }
        for c in cfg.IV_CURRENT_STEPS:
            r.update({f'IV_evoked_spikes_({c})pA':f'number of evoked spikes for {c}pA injected current.'})
        for c in cfg.IV_CURRENT_STEPS:
            r.update({f'IV_rebound_spikes_({c})pA':f'number of rebound spikes for {c}pA injected current.'})
        return r

    def results(self):
        self.r={}
        self.r['IV_baseline']                                        =np.nanmean([f.baseline for f in self.frames if f.enabled ]) / cfg.OUTPUT_V_SCALE
        self.r['IV_resistance']                                      =np.nanmean([f.resistance for f in self.frames if f.current<0 and f.sagratio>0.90 and f.enabled]) / cfg.OUTPUT_OHM_SCALE
        self.r['IV_resistance_interp']=np.nanmean([f.resistance_interp for f in self.frames if f.current<0 and f.enabled]) / cfg.OUTPUT_OHM_SCALE
        self.r['IV_tc']=np.nanmean([f.fitter.tc for f in self.frames if f.current<cfg.IV_TCFIT_THRESHOLD and f.enabled]) / cfg.OUTPUT_S_SCALE
        self.r[f'IV_sagratio_I={cfg.IV_SAG_TARGET_CURRENT}pA']           =np.nanmean([f.sagratio for f in self.frames if f.current==cfg.IV_SAG_TARGET_CURRENT and f.enabled])
        self.r[f'IV_sagratio_I={cfg.IV_SAG_TARGET_CURRENT}pA_pct']       =np.nanmean([f.sagratio_pct for f in self.frames if f.current==cfg.IV_SAG_TARGET_CURRENT and f.enabled])
        frames_for_sag=sorted([f for f in self.frames if f.enabled],key=lambda f:np.fabs((f.baseline-f.sagss)-cfg.IV_SAG_SS_TARGET_VOLTAGE))
        self.r[f'IV_sagratio_tgt={cfg.IV_SAG_SS_TARGET_VOLTAGE}V']       =frames_for_sag[0].sagratio
        self.r[f'IV_sagratio_tgt={cfg.IV_SAG_SS_TARGET_VOLTAGE}V_pct']   =frames_for_sag[0].sagratio_pct
        frames_with_evoked_spikes=[f for f in self.frames if f.current>=0 and len(f.evokedspikes)>0 and f.enabled]
        if len(frames_with_evoked_spikes)>0:
            self.r[f'IV_rheobase']=frames_with_evoked_spikes[0].current/1.0e12 / cfg.OUTPUT_A_SCALE
        ##
        frames_with_min_spikes=[f for f in self.frames if len(f.evokedspikes)>=cfg.IV_MIN_SPIKES_FOR_MEASURE and f.enabled]
        if len(frames_with_min_spikes)>0:
            reference_frame=frames_with_min_spikes[0]
            self.r['IV_avg_spike_threshold']                 =np.nanmean([s.threshold for s in reference_frame.evokedspikes]) / cfg.OUTPUT_V_SCALE
            self.r['IV_avg_spike_peak']                      =np.nanmean([s.peak for s in reference_frame.evokedspikes]) / cfg.OUTPUT_V_SCALE
            self.r['IV_avg_spike_amplitude']                 =np.nanmean([s.amplitude for s in reference_frame.evokedspikes]) / cfg.OUTPUT_V_SCALE
            self.r['IV_avg_spike_half_width']                =np.nanmean([s.halfwidth for s in reference_frame.evokedspikes]) / cfg.OUTPUT_S_SCALE
            self.r['IV_avg_spike_max_rise_slope']            =np.nanmean([s.maxrise for s in reference_frame.evokedspikes]) / cfg.OUTPUT_S_SCALE
            self.r['IV_avg_spike_max_fall_slope']            =np.nanmean([s.maxfall for s in reference_frame.evokedspikes]) / cfg.OUTPUT_S_SCALE
            self.r['IV_avg_spike_ahp']                       =np.nanmean([reference_frame.ahpbaseline-s.ahp for s in reference_frame.evokedspikes if s.complete ]) / cfg.OUTPUT_V_SCALE
            self.r['IV_avg_spike_thr2ahp']                   =np.nanmean([s.threshold-s.ahp for s in reference_frame.evokedspikes if s.complete ]) / cfg.OUTPUT_V_SCALE
            #same with first spike instead of average
            self.r['IV_first_spike_threshold']                 =reference_frame.evokedspikes[0].threshold / cfg.OUTPUT_V_SCALE
            self.r['IV_first_spike_peak']                      =reference_frame.evokedspikes[0].peak / cfg.OUTPUT_V_SCALE
            self.r['IV_first_spike_amplitude']                 =reference_frame.evokedspikes[0].amplitude / cfg.OUTPUT_V_SCALE
            self.r['IV_first_spike_half_width']                =reference_frame.evokedspikes[0].halfwidth / cfg.OUTPUT_S_SCALE
            self.r['IV_first_spike_max_rise_slope']            =reference_frame.evokedspikes[0].maxrise / cfg.OUTPUT_S_SCALE
            self.r['IV_first_spike_max_fall_slope']            =reference_frame.evokedspikes[0].maxfall / cfg.OUTPUT_S_SCALE
            if reference_frame.evokedspikes[0].complete:
                self.r['IV_first_spike_ahp']                   =(reference_frame.ahpbaseline-reference_frame.evokedspikes[0].ahp) / cfg.OUTPUT_V_SCALE
                self.r['IV_first_spike_thr2ahp']               =(reference_frame.evokedspikes[0].threshold-reference_frame.evokedspikes[0].ahp) / cfg.OUTPUT_V_SCALE
            else:
                self.r['IV_first_spike_ahp']                   =np.nan
                self.r['IV_first_spike_thr2ahp']               =np.nan
            ##
            self.r['IV_first_spike_delay']                   =(reference_frame.evokedspikes[0].time-cfg.IV_CURRENT_INJECTION_START) / cfg.OUTPUT_S_SCALE
        ## in order to compute ISI, we need at least 3 spikes!
        frames_with_min_spikes=[f for f in self.frames if len(f.evokedspikes)>=max(3,cfg.IV_MIN_SPIKES_FOR_MEASURE) and f.enabled]
        if len(frames_with_min_spikes)>0:
            reference_frame=frames_with_min_spikes[0]
            self.r['IV_first_spike_interval']                =reference_frame.evokedspikes[1].ISI / cfg.OUTPUT_S_SCALE
            self.r['IV_last_spike_interval']                 =reference_frame.evokedspikes[-1].ISI / cfg.OUTPUT_S_SCALE
            self.r['IV_first_div_last_spike_interval']       =self.r['IV_first_spike_interval']/self.r['IV_last_spike_interval']
        frames_with_max_spikes=sorted([f for f in self.frames if len(f.evokedspikes)>cfg.IV_MIN_SPIKES_FOR_SFADAPT and f.enabled],key=lambda f:len(f.evokedspikes))
        if len(frames_with_max_spikes)>0:
            self.r['IV_sfa_freq_lin']                        =frames_with_max_spikes[-1].sfa_freq_lin
            self.r['IV_sfa_freq_log']                        =frames_with_max_spikes[-1].sfa_freq_log
            self.r['IV_sfa_freq_div']                        =frames_with_max_spikes[-1].sfa_freq_div
            self.r['IV_sfa_peak_lin']                        =frames_with_max_spikes[-1].sfa_peak_lin
            self.r['IV_sfa_peak_log']                        =frames_with_max_spikes[-1].sfa_peak_log
            self.r['IV_sfa_peak_div']                        =frames_with_max_spikes[-1].sfa_peak_div
        fr=[f for f in self.frames if len(f.evokedspikes)>2]
        if len(fr):
            self.r['IV_half_width_ratio_3/1']                =fr[0].evokedspikes[2].halfwidth/fr[0].evokedspikes[0].halfwidth
            #self.r['IV_third_spike_threshold']               =fr[0].evokedspikes[2].threshold / cfg.OUTPUT_V_SCALE
            #self.r['IV_third_spike_peak']                    =fr[0].evokedspikes[2].peak / cfg.OUTPUT_V_SCALE
            #self.r['IV_third_spike_amplitude']               =fr[0].evokedspikes[2].amplitude / cfg.OUTPUT_V_SCALE
            self.r['IV_third_spike_half_width']              =fr[0].evokedspikes[2].halfwidth / cfg.OUTPUT_S_SCALE
            #self.r['IV_third_spike_max_rise_slope']          =fr[0].evokedspikes[2].maxrise / cfg.OUTPUT_S_SCALE
            #self.r['IV_third_spike_max_fall_slope']          =fr[0].evokedspikes[2].maxfall / cfg.OUTPUT_S_SCALE
        self.r['IV_max_nb_spikes']                           =np.max([len(f.evokedspikes) for f in self.frames])            
        self.r['IV_max_freq']                                =self.r['IV_max_nb_spikes'] /(cfg.IV_CURRENT_INJECTION_STOP-cfg.IV_CURRENT_INJECTION_START)
        for f in self.frames:
            self.r[f'IV_evoked_spikes_({f.current})pA']     =len(f.evokedspikes)
        for f in self.frames:
            self.r[f'IV_rebound_spikes_({f.current})pA']     =len(f.reboundspikes)
        frames_with_max_spikes=sorted(self.frames,key=lambda f:len(f.evokedspikes))
        self.r['IV_firing_pattern']                          =frames_with_max_spikes[-1].pattern
        self.r['IV_fano']                                    =frames_with_max_spikes[-1].fano
        ## custom measurements:
        extrameasurements={k:v for k,v in cfg.__dict__.items() if not k.isupper() and k.startswith('IV_')}
        for k,v in extrameasurements.items():
            try:
                self.r[k]=eval(v)
            except:
                self.r[k]="error running eval"

        return self.r

class rheobaseprotocol(BaseProtocol):
    def __init__(self,sigs,interactive):
        cfg.IV_CURRENT_INJECTION_START=cfg.RHEO_CURRENT_INJECTION_START
        cfg.IV_CURRENT_INJECTION_STOP=cfg.RHEO_CURRENT_INJECTION_STOP+0.05 ## a spike may occur short after end of pulse
        cfg.IV_BASELINE_START=cfg.RHEO_BASELINE_START
        cfg.IV_BASELINE_STOP=cfg.RHEO_BASELINE_STOP
        self.frames=[ivframe(s,idx=e,parent=self, current=5*e) for e,s in enumerate(sigs) ]
        ## get the first frame with at least one spike
        self.BaseFrame=[f for f in self.frames if len(f.evokedspikes)==0][-1].voltage
        ## rebuild list of frames
        # self.frames=[ivframe(s-self.BaseFrame,idx=e,parent=self, current=5*e) for e,s in enumerate(sigs) ]
        super(rheobaseprotocol,self).__init__(interactive)

    def provides(self):
        r={"RHEO_baseline":"average baseline (all frames)",
            'RHEO_rheobase':'current required to observe a spike between cfg.RHEO_CURRENT_INJECTION_START and cfg.RHEO_CURRENT_INJECTION_STOP.',
            'RHEO_spike_threshold':'spike threshold. computed on first frame with one spike.',
            'RHEO_spike_peak':'spike peak. computed on first frame with one spike.',
            'RHEO_spike_amplitude':'spike amplitude (=peak-threshold). computed on first frame with one spike.',
            'RHEO_spike_half_width':'spike half width (at (peak-threshold)/2). computed on first frame with one spike.',
            'RHEO_spike_max_rise_slope':'spike maximum rise slope. computed on first frame with one spike.',
            'RHEO_spike_max_fall_slope':'spike maximum fall slope. computed on first frame with one spike.',
            'RHEO_spike_ahp':'spike ahp. computed on first frame with one spike.',
        }
        return r

    def results(self):
        self.r={}
        self.r['RHEO_baseline']                                        =np.nanmean([f.baseline for f in self.frames if f.enabled ]) / cfg.OUTPUT_V_SCALE
        frames_with_evoked_spikes=[f for f in self.frames if f.current>=0 and len(f.evokedspikes)>0 and f.enabled]
        if len(frames_with_evoked_spikes)>0:
            self.r[f'RHEO_rheobase']=frames_with_evoked_spikes[0].current/1.0e12 / cfg.OUTPUT_A_SCALE
        ##
        frames_with_min_spikes=[f for f in self.frames if len(f.evokedspikes)==1 and f.enabled]
        if len(frames_with_min_spikes)>0:
            reference_frame=frames_with_min_spikes[0]
            self.r['RHEO_spike_threshold']                 =reference_frame.evokedspikes[0].threshold / cfg.OUTPUT_V_SCALE
            self.r['RHEO_spike_peak']                      =reference_frame.evokedspikes[0].peak  / cfg.OUTPUT_V_SCALE
            self.r['RHEO_spike_amplitude']                 =reference_frame.evokedspikes[0].amplitude  / cfg.OUTPUT_V_SCALE
            self.r['RHEO_spike_half_width']                =reference_frame.evokedspikes[0].halfwidth / cfg.OUTPUT_S_SCALE
            self.r['RHEO_spike_max_rise_slope']            =reference_frame.evokedspikes[0].maxrise  / cfg.OUTPUT_S_SCALE
            self.r['RHEO_spike_max_fall_slope']            =reference_frame.evokedspikes[0].maxfall  / cfg.OUTPUT_S_SCALE
            if reference_frame.idx==0:
                self.r['RHEO_spike_ahp']=np.nan
            else:
                t0=reference_frame.evokedspikes[0].time-0.005
                t1=reference_frame.evokedspikes[0].time+0.05
                sub=self.frames[reference_frame.idx].voltage-self.frames[reference_frame.idx-1].voltage
                plt.plot(sub.ms(),sub.mV())
                plt.plot(sub.ms(t0,t1),sub.mV(t0,t1))
                plt.pause(-1)
                self.r['RHEO_spike_ahp']=np.min(sub.V(t0,t1))  / cfg.OUTPUT_V_SCALE
        return self.r

class spontaneousactivityprotocol(BaseProtocol):
    def __init__(self,sigs,interactive):
        ## awfull hack here:
        ## ivframe calculates baseline for  AHP between cfg.IV_CURRENT_INJECTION_START and cfg.IV_CURRENT_INJECTION_STOP
        ## as we want to take baseline for all trace, we save these values for later restoration, and update the values...
        ## may not be necessary as params are reparsed before every protocol analysis...
        #oldstart, oldstop= cfg.IV_CURRENT_INJECTION_START, cfg.IV_CURRENT_INJECTION_STOP
        cfg.IV_CURRENT_INJECTION_START, cfg.IV_CURRENT_INJECTION_STOP=0, sigs[0].times.magnitude.flatten()[-1]
        self.frames=[ivframe(s,idx=0,parent=self,current=0) for e,s in enumerate(sigs) ]
        super(spontaneousactivityprotocol,self).__init__(interactive)
    def provides(self):
        return {'SPON_baseline':'average baseline.',
                'SPON_frequency':'average frequency.',
                'SPON_avg_spike_threshold':'spike threshold.',
                'SPON_avg_spike_peak':'spike peak.',
                'SPON_avg_spike_amplitude':'spike amplitude (=peak-threshold).',
                'SPON_avg_spike_half_width':'spike half width (at (peak-threshold)/2).',
                'SPON_avg_spike_max_rise_slope':'spike maximum rise slope.',
                'SPON_avg_spike_max_fall_slope':'spike maximum fall slope.',
                'SPON_avg_spike_ahp':'spike ahp.',
                'SPON_fano':'fano factor',
                }

    def results(self):
        self.r={}
        self.r['SPON_baseline']=self.frames[0].ahpbaseline/cfg.OUTPUT_V_SCALE
        self.r['SPON_frequency']=len(self.frames[0].spikes)/(cfg.IV_CURRENT_INJECTION_STOP - cfg.IV_CURRENT_INJECTION_START)
        if len(self.frames[0].spikes)>0:
            self.r['SPON_avg_spike_threshold']=np.nanmean([s.threshold for s in self.frames[0].spikes])/cfg.OUTPUT_OHM_SCALE
            self.r['SPON_avg_spike_peak']=np.nanmean([s.peak for s in self.frames[0].spikes])/cfg.OUTPUT_V_SCALE
            self.r['SPON_avg_spike_amplitude']=np.nanmean([s.amplitude for s in self.frames[0].spikes])/cfg.OUTPUT_V_SCALE
            self.r['SPON_avg_spike_half_width']=np.nanmean([s.halfwidth for s in self.frames[0].spikes])/cfg.OUTPUT_S_SCALE
            self.r['SPON_avg_spike_max_rise_slope']=np.nanmean([s.maxrise for s in self.frames[0].spikes])
            self.r['SPON_avg_spike_max_fall_slope']=np.nanmean([s.maxfall for s in self.frames[0].spikes])
            self.r['SPON_avg_spike_ahp']=np.nanmean([s.ahp for s in self.frames[0].spikes if s.complete])/cfg.OUTPUT_V_SCALE
            self.r['SPON_fano']=self.frames[0].fano
        return self.r

class foldernameprotocol:
    def __init__(self,fpath, interactive=True):
        self.r={'_FOLD_fullpath':None,'_FOLD_filename':None}
        if os.path.isfile(fpath):
            self.r['_FOLD_filename']=Path(fpath).name
            fpath=str(Path(fpath).parent)
        if os.path.isdir(fpath):
            self.r['_FOLD_filename']=Path(fpath).name
            self.fpath=str(fpath)
    def provides(self):
        keys=cfg.FOLDER_NAMING_SCHEME.split(cfg.FOLDER_NAMING_SEP)
        r={'_FOLD_fullpath':'fullpath to folder',
           '_FOLD_filename':'the file or folder name'}
        r.update({'_FOLD_'+k:'no description' for k in keys})
        return r
    def results(self):
        keys=cfg.FOLDER_NAMING_SCHEME.split(cfg.FOLDER_NAMING_SEP)
        try:
            values=str(Path(self.fpath).name).split(cfg.FOLDER_NAMING_SEP)
            self.r.update({'_FOLD_'+k:v for k,v in zip(keys,values)})
        except:
            logging.getLogger(__name__).warning("Inconsistent folder naming. Check cfg.FOLDER_NAMING_SCHEME and cfg.FOLDER_NAMING_SEP values")
            self.r.update({'_FOLD_'+k:None for k in keys })
            self.r.update({'_FOLD_fullpath':self.fpath})
        return self.r

class resonnanceframe(BaseFrame):
    def __init__(self,sig,current,idx, parent):
        self.voltage=sig
        self.sr=int(sig.sampling_rate)
        self.current=current
        self.start=0
        self.stop=len(self.voltage)
        super(resonnanceframe,self).__init__(idx,parent)
    
    def process(self,bitmask=0xFFFF):
        self.start=int(_clamp(self.start,0,len(self.voltage)))
        self.stop=int(_clamp(self.stop,0,len(self.voltage)))
        volts=self.voltage.V()[self.start:self.stop]
        ref=self.current.A()[self.start:self.stop]
        self.amplitude=int(5*np.rint((np.max(ref)-np.min(ref))*1e11)) ## round to nearest integer
        if not self.amplitude in cfg.RES_AMPLITUDES:
            logging.getLogger(__name__).warning(f"Unexpected current amplitude in resonnance protocol {self.amplitude}")
        self.sig_freq,self.sig_pow=scipy.signal.periodogram(volts,fs=self.voltage._sampling_rate)
        self.ref_freq,self.ref_pow=scipy.signal.periodogram(ref,fs=self.current._sampling_rate)
        ## but floating point divisions with numbers in 10e-6/10e-24 range seems to mess up python!
        ## convert to mV and pA 
        self.ref_pow*=1e24 ## 1pA**2
        self.sig_pow*=1e6  ## 1mV**2

        self.impedence=self.sig_pow/self.ref_pow
        self.keep=np.where((self.sig_freq<cfg.RES_HIGH_BAND)&(self.sig_freq>cfg.RES_LOW_BAND))
        self.res_pos=np.argmax(self.impedence[self.keep])
        self.res_freq=float(self.ref_freq[self.keep][self.res_pos])
        self.res_imp=float(self.impedence[self.keep][self.res_pos])
        self.imp05=float(self.impedence[np.argmin(np.abs(self.sig_freq - 0.5*pq.Hz))])
    
    @once
    def setup(self):
        #self._fig().subplots(3, 1,sharex = True)
        self._fig().subplots(4, 1)
        self._axes(1).sharex(self._axes(0))
        self._axes(2).sharex(self._axes(0))
        self._cursor(self._axes(3),'v',self.start,
                    lambda x:self.parent.currentframe().__setattr__('start',x) or \
                        self.parent.process() or \
                        self.parent.draw (True)
                    )
        self._cursor(self._axes(3),'v',self.stop,
                    lambda x:self.parent.currentframe().__setattr__('stop',x) or \
                        self.parent.process() or \
                        self.parent.draw (True)
                    )

    def draw(self,drawall=True):
        self.setup() ## ensure that axes are ready!
        self._fig().canvas.TopLevelParent.SetTitle("Reonnance protocol")
        self._fig().suptitle(f"res_freq: {self.res_freq:.2f} res_imp {self.res_imp*1e9/cfg.OUTPUT_OHM_SCALE:.2f} 0.5Hz_imp {self.imp05*1e9/cfg.OUTPUT_OHM_SCALE:.2f}" )
        if drawall:  ## avoid redrawing signals if not required
            self._clf(['traces'])
            self._axes(0).loglog(self.sig_freq[self.keep],self.sig_pow[self.keep],c='#1f77b4',gid="traces")
            #self._axes(0).set_title("Voltage power spectrum",fontdict={'fontsize':10})
            _autoscale(self._axes(0),self.sig_freq[self.keep],self.sig_pow[self.keep])
            self._axes(1).loglog(self.ref_freq[self.keep],self.ref_pow[self.keep],c='#1f77b4',gid="traces")
            #self._axes(1).set_title("Current power spectrum",fontdict={'fontsize':10})
            _autoscale(self._axes(1),self.ref_freq[self.keep],self.ref_pow[self.keep])
            self._axes(2).loglog(self.ref_freq[self.keep],self.impedence[self.keep],c='#1f77b4',gid="traces")
            #self._axes(2).set_title("Impedance",fontdict={'fontsize':10})
            _autoscale(self._axes(2),self.ref_freq[self.keep],self.impedence[self.keep])
            self._axes(3).plot(self.voltage.mV(), color='k',gid="traces")
            #self._axes(3).set_title("Voltage",fontdict={'fontsize':10})
        self._clf(['markers'])
        self._axes(2).loglog([self.res_freq],self.res_imp,'o',color='orange',gid="markers")
        self._axes(2).loglog([0.5],self.imp05,'x',color='green',gid="markers")
        self._fig().tight_layout()

class resonnanceprotocol(BaseProtocol):
    def __init__(self,sigs,interactive):
        self.frames=[ resonnanceframe(sigs[0],sigs[1],idx=0,parent=self)  ]
        super(resonnanceprotocol,self).__init__(interactive)
    def provides(self):
        r={}
        for amp in cfg.RES_AMPLITUDES:
            r.update({f'RES_resonnance_{amp}pA':'resonnance frequency',
                f'RES_impedance_{amp}pA':'impedence of neurone at resonnance frequency',
                f'RES_impedance_05Hz_{amp}pA':'impedence of neurone at 0.5Hz'}
            )
        return r
    def results(self):
        self.r= {f'RES_resonnance_{self.frames[0].amplitude}pA':float(self.frames[0].res_freq),
                f'RES_impedance_{self.frames[0].amplitude}pA':1e6*float(self.frames[0].res_imp*1000)/cfg.OUTPUT_OHM_SCALE,
                f'RES_impedance_05Hz_{self.frames[0].amplitude}pA':1e6*float(self.frames[0].imp05*1000)/cfg.OUTPUT_OHM_SCALE}
        return self.r

class rampframe(BaseFrame):
    def __init__(self,sig,voltage,idx, parent):
        self.current=sig
        self.sr=int(sig.sampling_rate)
        self.voltage=voltage
        super(rampframe,self).__init__(idx,parent)
    
    def process(self,bitmask=0xFFFF):
        volts=self.voltage.V()
        amps=self.current.A()
        self.fitter1=XYFitter(self.current.s(cfg.RAMP_BOUNDARIES[0],cfg.RAMP_BOUNDARIES[0]+0.2),
                              self.current.pA(cfg.RAMP_BOUNDARIES[0],cfg.RAMP_BOUNDARIES[0]+0.2),
                              0,True,
                              maxfev=cfg.ITSQ_FIT_ITERATION_COUNT,
                              version=cfg.ITSQ_FITTER_VERSION)
        times1=self.current.s(cfg.RAMP_BOUNDARIES[0],cfg.RAMP_BOUNDARIES[1])
        self.line1=[times1,self.fitter1.line(times1)]
        self.fitter2=XYFitter(self.current.s(cfg.RAMP_BOUNDARIES[1]-0.2,cfg.RAMP_BOUNDARIES[1]),
                              self.current.pA(cfg.RAMP_BOUNDARIES[1]-0.2,cfg.RAMP_BOUNDARIES[1]),
                              0,True,
                              maxfev=cfg.ITSQ_FIT_ITERATION_COUNT,
                              version=cfg.ITSQ_FITTER_VERSION)
        times2=self.current.s(cfg.RAMP_BOUNDARIES[0],cfg.RAMP_BOUNDARIES[1])
        self.line2=[times2,self.fitter2.line(times2)]

    @once
    def setup(self):
        self._fig().subplots(2, 1,gridspec_kw={'height_ratios': [3, 1],"top":0.9},sharex = True)
        ## tried with for loop and partial, but does not work!
        self._cursor(self._axes(),'v',cfg.RAMP_BOUNDARIES[0],
                lambda x:cfg.RAMP_BOUNDARIES.__setitem__(0,x) or self.parent.process(ivframe.bitmask_SPIKES) or self.parent.draw (False)
                )
        self._cursor(self._axes(),'v',cfg.RAMP_BOUNDARIES[1],
                lambda x:cfg.RAMP_BOUNDARIES.__setitem__(1,x) or self.parent.process(ivframe.bitmask_SPIKES) or self.parent.draw (False)
                )
        self._cursor(self._axes(),'v',cfg.RAMP_BOUNDARIES[2],
                lambda x:cfg.RAMP_BOUNDARIES.__setitem__(1,x) or self.parent.process(ivframe.bitmask_SPIKES) or self.parent.draw (False)
                )
        self._cursor(self._axes(),'v',cfg.RAMP_BOUNDARIES[3],
                lambda x:cfg.RAMP_BOUNDARIES.__setitem__(1,x) or self.parent.process(ivframe.bitmask_SPIKES) or self.parent.draw (False)
                )

    def draw(self,drawall=True):
        self.setup() ## ensure that axes are ready!
        self._fig().canvas.TopLevelParent.SetTitle("Ramp protocol")
        if drawall:  ## avoid redrawing signals if not required
            self._clf(['traces'])
            self._axes(0).plot(self.current.s(),self.current.pA(),color='blue',gid='traces')
            self._axes(1).plot(self.voltage.s(),self.voltage.mV(),color='green',gid='traces')
        self._clf(['markers'])
        if self.fitter1.success:
           self._axes(0).plot(*self.line1,color='red',gid='markers')
        if self.fitter2.success:
           self._axes(0).plot(*self.line2,color='darkred',gid='markers')

class rampprotocol(BaseProtocol):
    def __init__(self,sigs,interactive):
        self.frames=[ rampframe(sig[0],sig[1],idx=0,parent=self) for sig in sigs ]
        super(rampprotocol,self).__init__(interactive)
    def provides(self):
        return {'RAMP_slope_-40':'slope at Vhold=-40mV (pA/s)',
                'RAMP_slope_-120':'slope at Vhold=-120mV (pA/s)',
                'RAMP_iorect_40_over_120':'ratio of the slopes',
                }
    def results(self):
        self.r= {'RAMP_slope_-40':np.nanmean([f.fitter1.a for f in self.frames if f.enabled]),
                 'RAMP_slope_-120':np.nanmean([f.fitter2.a for f in self.frames if f.enabled]),
                 'RAMP_iorect_40_over_120':np.nanmean([f.fitter1.a/f.fitter2.a for f in self.frames if f.enabled]),
                }
        return self.r
##################################################################################################
##################################################################################################
##################################################################################################
## END OF PROTOCOLS SECTION
##################################################################################################
##################################################################################################
##################################################################################################

##################################################################################################
##################################################################################################
##################################################################################################
## PREPROCESS AND DISPATCH FILES
##################################################################################################
##################################################################################################
##################################################################################################

def HOOK_ADJUST_STEP_HEIGHT():
    ## this hook attempts to correct step protocol amplitude
    ## when parsing protocol in axgd / axgx files, we can read the start level and level inc rement,
    ## but the units are unknown (sometimes pA, sometimes nA)
    ## this hook will divide all values by 1000 if values are all higher than 2nA
    if not cfg.ITSQ_ENABLE_HOOKS:
        return
    if all([abs(s)>=2000 for s in cfg.IV_CURRENT_STEPS if s!=0]):
        logging.getLogger(__name__).warning("Attempting to rescale pA to nA in axg* protocol")
        cfg.IV_CURRENT_STEPS=[s//1000 for s in cfg.IV_CURRENT_STEPS]
    if all([abs(s)>=2000 for s in cfg.SAG_CURRENT_STEPS if s!=0]):
        logging.getLogger(__name__).warning("Attempting to rescale pA to nA in axg* protocol")
        cfg.SAG_CURRENT_STEPS=[s//1000 for s in cfg.SAG_CURRENT_STEPS]
    if abs(cfg.INPUTR_CURRENT_STEP)>1000:
        logging.getLogger(__name__).warning("Attempting to rescale pA to nA in axg* protocol")
        cfg.INPUTR_CURRENT_STEP=cfg.INPUTR_CURRENT_STEP//1000
    ## same for sag protocol!


def process_file(inpath):
    cfg.parse(Path(__file__).resolve().parent/gen_cfg_file) ## gen_cfg_file already contains the params folder!
    neuronprops={}
    protocol=None
    if str(Path(inpath).name)[0] in cfg.ITSQ_SKIP_FILES:
        logging.getLogger(__name__).info(f"Skipping file {str(inpath)}")
        return {}
    myexp=Experiment(inpath)
    protocolname=myexp.protocol.name
    logging.getLogger(__name__).info(f"{protocolname} : {str(inpath)}")
    if any([fnmatch.fnmatchcase(protocolname,x) for x in cfg.IV_PROTOCOL_NAMES])  and 'iv' in cfg.PROCESS_PROTOCOLS:
        cfg.parse(Path(__file__).resolve().parent/"params"/(protocolname+"_params.py"))
        sigs=myexp.signal(0)
        if cfg.ITSQ_PARSE_PROTOCOLS: ## get pulses info
            cfg.IV_CURRENT_INJECTION_START=myexp.protocol.ascurrentsteps()['steps'][0]['start']
            cfg.IV_CURRENT_INJECTION_STOP=myexp.protocol.ascurrentsteps()['steps'][0]['stop']
            cfg.IV_CURRENT_STEPS=[step['lvl'] for step in myexp.protocol.ascurrentsteps()['steps'] ]
            HOOK_ADJUST_STEP_HEIGHT()
        ## detect start and stop. not heavily tested, but should be ok for simple square pulses
        protocol=ivprotocol(sigs,cfg.IV_DEBUG_FRAME)
        neuronprops.update(protocol.results())

    ## processing AHPVprotocol protocol 
    elif any([fnmatch.fnmatchcase(protocolname,x) for x in cfg.AHPV_PROTOCOL_NAMES])  and 'ahpv' in cfg.PROCESS_PROTOCOLS :
        cfg.parse(Path(__file__).resolve().parent/"params"/(protocolname+"_params.py"))
        sigs=myexp.signal(0)
        assert(len(cfg.AHPV_FREQS)==len(sigs))
        for idx,s in enumerate(sigs):
            apcount=int(protocolname[0])
            freq=cfg.AHPV_FREQS[idx]
            cfg.AHP_VALID_COMBO.append((apcount,freq))
            protocol=ahpprotocol([s],cfg.AHP_DEBUG_FRAME,freq,apcount)
            neuronprops.update(protocol.results())

    ## processing AHPprotocol protocol 
    elif any([fnmatch.fnmatchcase(protocolname,x) for x in cfg.AHP_PROTOCOL_NAMES])  and 'ahp' in cfg.PROCESS_PROTOCOLS :
        cfg.parse(Path(__file__).resolve().parent/"params"/(protocolname+"_params.py"))
        sigs=myexp.signal(0)
        ## read frequency from protocol name
        if cfg.AHP_CHECK_NONE:
            #apstr=re.search(r'\d*AP',protocolname,re.MULTILINE)
            ## obviously the protocol same is not consistent between 5AP procotols and 15 AP protocols. The following regexp should match both
            freqstr=re.search(r'\d+[ ]{0,1}[H,h]z',protocolname,re.MULTILINE)
            apstr=re.search(r'\d+[ ]{0,1}A[H]{0,1}P',protocolname,re.MULTILINE)
            if freqstr:
                freq=int(''.join(filter(str.isdigit, freqstr.group(0))))
                #freq=int(freqstr.group(0)[:-2])
                logging.getLogger(__name__).info(f"AHP Protocol indicates {freq}Hz")
            else:
                logging.getLogger(__name__).warning("Could not extract frequency from AHP protocol")
                freq=None
            if apstr:
                apcount=int(''.join(filter(str.isdigit, apstr.group(0))))
                #apcount=int(apstr.group(0)[:-1])
                logging.getLogger(__name__).info(f"AHP Protocol indicates {apcount} APs")
            else:
                logging.getLogger(__name__).warning("Could not extract number of APs from AHP protocol")
                apcount=None
        else:
            freq=None
            apcount=None
        ## AF version has one frame, whereas I have many frames... Just keep the last one
        protocol=ahpprotocol([sigs[-1]],cfg.AHP_DEBUG_FRAME,freq,apcount)
        ##protocol=ahpprotocol(sigs,cfg.AHP_DEBUG_FRAME,freq)
        neuronprops.update(protocol.results())
        
    ## processing ZAP protocol
    elif any([fnmatch.fnmatchcase(protocolname,x) for x in cfg.ZAP_PROTOCOL_NAMES]) and 'resonnance' in cfg.PROCESS_PROTOCOLS:
        cfg.parse(Path(__file__).resolve().parent/"params"/(protocolname+"_params.py"))
        sigs=myexp.signal(0)
        ## quite complex here! on some setups / protocols, the current is not recorded, so we have to load an external stimulus file!
        try:
            current=myexp.signal(1)
        except:
            ## too much variation in protol names here. force load current with exact same name as protocol 
            reffilepath=str(Path(__file__).resolve().parent/"resources"/protocolname)
            values=np.loadtxt(reffilepath+'.txt',delimiter='\t',skiprows=1,usecols=1)
            current=[neo.AnalogSignal(values, units=pq.A,sampling_rate=sigs[0].sampling_rate)]
        resonnance_error_string='''
        Your protocol does not include Current recording. 
        Moreover, the sampling/frequency/duration is not compatible with the stored protocol frequency/duration.
        Can't process that file unless you provide a valid protocol
        '''
        #assert(sigs[0].sampling_rate==current[0].sampling_rate)
        #assert(len(sigs[0])==len(current[0]))
        if len(sigs[0])==len(current[0]):
            protocol=resonnanceprotocol([sigs[0],current[0]],cfg.RES_DEBUG_FRAME)
            neuronprops.update(protocol.results())
        else:
            logging.getLogger(__name__).error(resonnance_error_string)
            return {}

    ## processing Time Constant protocol
    elif any([fnmatch.fnmatchcase(protocolname,x) for x in cfg.TC_PROTOCOL_NAMES])  and 'timeconstant' in cfg.PROCESS_PROTOCOLS:
        cfg.parse(Path(__file__).resolve().parent/"params"/(protocolname+"_params.py"))
        sigs=myexp.signal(0)
        if cfg.ITSQ_PARSE_PROTOCOLS: ## get pulses info
            cfg.TC_FIT_START=myexp.protocol.ascurrentsteps()['steps'][0]['stop']+0.001
            #cfg.TC_FIT_STOP=myexp.protocol.ascurrentsteps()['steps'][0]['stop'] ##dynamic var
            #cfg.TC_FIT_CURRENT_STEPS=[myexp.protocol.ascurrentsteps()['steps'][i]['lvl'] for i in range()
            #print(cfg.TC_FIT_CURRENT_STEPS)
        protocol=timeconstantprotocol(sigs,cfg.TC_DEBUG_FRAME)
        neuronprops.update(protocol.results())
    
    ## processing resistance protocol
    elif any([fnmatch.fnmatchcase(protocolname,x) for x in cfg.INPUTR_PROTOCOL_NAMES])  and 'resistance' in cfg.PROCESS_PROTOCOLS:
        cfg.parse(Path(__file__).resolve().parent/"params"/(protocolname+"_params.py"))
        sigs=myexp.signal(0)
        ## for resistance, average signals
        avgsig=neo.AnalogSignal( np.mean(np.array([s.magnitude.flatten() for s in sigs]),axis=0),
            units='V', 
            sampling_rate=sigs[0].sampling_rate
            )
        if cfg.ITSQ_PARSE_PROTOCOLS: ## get pulses info
            cfg.INPUTR_CURRENT_INJECTION_START=myexp.protocol.ascurrentsteps()['steps'][0]['start']
            cfg.INPUTR_CURRENT_INJECTION_STOP=myexp.protocol.ascurrentsteps()['steps'][0]['stop']
            cfg.INPUTR_CURRENT_STEP=myexp.protocol.ascurrentsteps()['steps'][0]['lvl']
            HOOK_ADJUST_STEP_HEIGHT()
        protocol=resistanceprotocol([avgsig],cfg.INPUTR_DEBUG_FRAME,currentstep=cfg.INPUTR_CURRENT_STEP)
        neuronprops.update(protocol.results())

    ## processing sag protocol
    elif any([fnmatch.fnmatchcase(protocolname,x) for x in cfg.SAG_PROTOCOL_NAMES])  and 'sag' in cfg.PROCESS_PROTOCOLS:
        cfg.parse(Path(__file__).resolve().parent/"params"/(protocolname+"_params.py"))
        sigs=myexp.signal(0)
        ## for sag, average signals by groups of 3
        from neomonkey import average,groupaverage
        #cnt=cfg.SAG_AVERAGE_COUNT
        cnt=myexp.protocol.episode_repeat
        #avgsig=[average(sigs[cnt*i],sigs[cnt*i+1],sigs[cnt*i+2]) for i in range(len(sigs)//cnt) ]
        avgsig=groupaverage(sigs,cnt,'framerepeat')
        if cfg.ITSQ_PARSE_PROTOCOLS: ## get pulses info
            cfg.SAG_CURRENT_INJECTION_START=myexp.protocol.ascurrentsteps()['steps'][0]['start']
            cfg.SAG_CURRENT_INJECTION_STOP=myexp.protocol.ascurrentsteps()['steps'][0]['stop']
            cfg.SAG_CURRENT_STEPS=[step['lvl'] for step in myexp.protocol.ascurrentsteps()['steps'] ]
            cfg.SAG_CURRENT_STEPS=sorted(list(set(cfg.SAG_CURRENT_STEPS)))
            HOOK_ADJUST_STEP_HEIGHT()
        protocol=sagprotocol(avgsig,cfg.SAG_DEBUG_FRAME,currentstep=cfg.SAG_CURRENT_STEPS)
        neuronprops.update(protocol.results())

    ## spontaneous activity protocol
    elif any([fnmatch.fnmatchcase(protocolname,x) for x in cfg.SPONTANEOUS_PROTOCOL_NAMES])  and 'spontaneousactivity' in cfg.PROCESS_PROTOCOLS:
        cfg.parse(Path(__file__).resolve().parent/"params"/(protocolname+"_params.py"))
        sigs=myexp.signal(0)
        cfg.IV_CURRENT_INJECTION_START, cfg.IV_CURRENT_INJECTION_STOP=0, sigs[0].times.magnitude.flatten()[-1]
        protocol=spontaneousactivityprotocol(sigs,cfg.SPONTANEOUS_DEBUG_FRAME)
        neuronprops.update(protocol.results())

    ## ramp protocol
    elif any([fnmatch.fnmatchcase(protocolname,x) for x in cfg.RAMP_PROTOCOL_NAMES])  and 'ramp' in cfg.PROCESS_PROTOCOLS:
        cfg.parse(Path(__file__).resolve().parent/"params"/(protocolname+"_params.py"))
        sigs=myexp.signal(0)
        voltage=myexp.signal(1)
        protocol=rampprotocol([ (sigs[e],voltage[e]) for e in range(len(sigs))],cfg.RAMP_DEBUG_FRAME)
        neuronprops.update(protocol.results())

    ## rheobase protocol
    elif any([fnmatch.fnmatchcase(protocolname,x) for x in cfg.RHEO_PROTOCOL_NAMES])  and 'rheobase' in cfg.PROCESS_PROTOCOLS:
        cfg.parse(Path(__file__).resolve().parent/"params"/(protocolname+"_params.py"))
        sigs=myexp.signal(0)
        protocol=rheobaseprotocol([ sigs[e] for e in range(len(sigs))],cfg.RHEO_DEBUG_FRAME)
        neuronprops.update(protocol.results())

    ## unknown protocol/disabled protocol. warn the user
    else:
        logging.getLogger(__name__).warning(f"Unknown / disabled protocol {protocolname}. Check protocol association and PROCESS__ flags.")
    
    if not protocol is None:
        if cfg.ITSQ_PROTOCOL_SAVE_DATA:protocol.savedata(inpath,protocolname)
    
    return neuronprops

def processfolder(fpath):
    ## get meta info from folder
    neuronprops={}
    protocol=foldernameprotocol(fpath)
    neuronprops.update(protocol.results())
    ## search all files with required extension _prefix(cfg.PROCESS_EXTENSIONS,'*')
    allfiles=[f for ext in _prefix(cfg.PROCESS_EXTENSIONS,'*') for f in fpath.glob(ext) ]
    for inpath in allfiles:
        neuronprops.update(process_file(inpath))
    return neuronprops

def process(inpath,disable_filter=False):
    cfg.parse(Path(__file__).resolve().parent/gen_cfg_file)
    ## start processing
    allneurons=[]
    ## single file
    if Path(inpath).is_file() and Path(inpath).suffix in _prefix(cfg.PROCESS_EXTENSIONS,''):
        neuron={}
        neuron.update(process_file(Path(inpath)))
        allneurons.append(neuron)

    ## folder with files
    if Path(inpath).is_dir():
        if len([f for ext in _prefix(cfg.PROCESS_EXTENSIONS,'*') for f in Path(inpath).glob(ext) ])>0:
            neuron={}
            neuron.update(processfolder(Path(inpath)))
            allneurons.append(neuron)
        else:
            ## folder with mess
            folders=set([f.parents[0] for ext in _prefix(cfg.PROCESS_EXTENSIONS,'**/*') for f in Path(inpath).glob(ext) ])
            for folder in folders:
                neuron={}
                neuron.update(processfolder(folder))
                allneurons.append(neuron)
    ## before we output to csv,excel, ..., we have to make sure that we have exactly the same fields for all neurons
    ## fortunately, pandas takes care of this for us, provided that an index is given
    df=pd.DataFrame(allneurons).T
    ## optionnally read output fields from specified file
    ## python should be easy to read! sorry!
    ## filtering is now performed dynamically when updating grid
    '''
    if cfg.ITSQ_OUTPUT_FIELDS_FILE and not disable_filter:
        if (Path(__file__).resolve().parent/cfg.ITSQ_OUTPUT_FIELDS_FILE).is_file():
            outfields=[ l.split("#")[0].rstrip(' \t\n\r').lstrip('+-#')                         \
                        for l in open(Path(__file__).resolve().parent/cfg.ITSQ_OUTPUT_FIELDS_FILE)  \
                        if not ( l.split("#")[0].startswith('-') or \
                                l.split("#")[0].startswith('#') or \
                                len(l.split("#")[0].strip(' \t\n\r')) == 0
                                )
                    ]
        else:
            logging.getLogger(__name__).info("Could not find list of output parametes. Generating one")
            outfields=[ k for pname in cfg.PROCESS_PROTOCOLS for k in globals()[pname+"protocol"].provides(None).keys()]
            with open(Path(__file__).resolve().parent/cfg.ITSQ_OUTPUT_FIELDS_FILE,'w') as outfile:
                outfile.writelines([l+"\n" for l in outfields])
        discarded=[p for p in df.index if not p in outfields]
        for p in discarded:
            logging.getLogger(__name__).warning(f"parameter {p} is rejected by output configuration ")
        df=df.reindex(outfields)
    '''
    if cfg.OUTPUT_CSV:        df.to_csv("results.csv",sep=cfg.OUTPUT_CSVSEP)
    if cfg.OUTPUT_JSON:       df.to_json("results.json")
    if cfg.OUTPUT_EXCEL:      df.to_excel("results.xlsx")
    if cfg.OUTPUT_CLIPBOARD:
        ## to_clipboard behavior has changed recently...
        df.to_clipboard(excel=cfg.OUTPUT_CLIPBOARD_EXCEL,index=cfg.OUTPUT_CLIPBOARD_ROWNAMES)
    return df

def filterfields():
    if (Path(__file__).resolve().parent/cfg.ITSQ_OUTPUT_FIELDS_FILE).is_file():
        outfields=[ l.split("#")[0].rstrip(' \t\n\r').lstrip('+-#')                         \
                    for l in open(Path(__file__).resolve().parent/cfg.ITSQ_OUTPUT_FIELDS_FILE)  \
                    if not ( l.split("#")[0].startswith('-') or \
                            l.split("#")[0].startswith('#') or \
                            len(l.split("#")[0].strip(' \t\n\r')) == 0
                            )
                    ]
    else:
        logging.getLogger('myapp').info("Could not find list of output parameters. Generating one")
        outfields=[ k for pname in cfg.PROCESS_PROTOCOLS for k in globals()[pname+"Protocol"].provides(None).keys()]
        with open(Path(__file__).resolve().parent/cfg.ITSQ_OUTPUT_FIELDS_FILE,'w') as outfile:
            outfile.writelines([l+"\n" for l in outfields])
    return outfields

if __name__=='__main__':
    ##CCSteps,abf, positive and negative
    #ROOTPATH="D:\\data-yves\\labo\\projects\\Patch-Seq-GADGFP\\Cell_Recordings\\20211215_85n\\20211215_85n_0002.abf"
    #ROOTPATH="D:\\data-yves\\labo\\projects\\Patch-Seq-GADGFP\\Cell_Recordings\\20211215_85n\\20211215_85n_0003.abf"
    ##Time constant
    #ROOTPATH="D:\\data-yves\\labo\\devel\\intrinsic\\samples\\yukti&clara\\WTC1-V2.2-12w-A1-DIV24-2022.03.11-Cell4\\WTC1-V2.2-12w-A1-DIV24-2022.03.11 cell4 004.axgd"
    ##resistance
    #ROOTPATH="D:\\data-yves\\labo\\devel\\intrinsic\\samples\\yukti&clara\\WTC1-V2.2-12w-A1-DIV24-2022.03.11-Cell4\\WTC1-V2.2-12w-A1-DIV24-2022.03.11 cell4 005.axgd"
    ##AHP_MED
    #ROOTPATH="D:\\data-yves\\labo\\devel\\intrinsic\\samples\\yukti&clara\\WTC1-V2.2-12w-A1-DIV24-2022.03.11-Cell2\\WTC1-V2.2-12w-A1-DIV24-2022.03.11 cell2 010.axgd"
    ##AHP_SLOW
    #ROOTPATH="D:\\data-yves\\labo\\devel\\intrinsic\\samples\\yukti&clara\\WTC1-V2.2-12w-A1-DIV24-2022.03.11-Cell2\\WTC1-V2.2-12w-A1-DIV24-2022.03.11 cell2 011.axgd"
    ## IV
    ROOTPATH="D:\\data-yves\\labo\\devel\\intrinsic\\samples\\yukti&clara\\WTC1-V2.2-12w-A1-DIV24-2022.03.11-Cell2\\WTC1-V2.2-12w-A1-DIV24-2022.03.11 cell2 001.axgd"
    #ROOTPATH="D:\\data-yves\\labo\\devel\\intrinsic\\samples\\yukti&clara\\WTC1-V2.2-12w-A1-DIV24-2022.03.11-Cell1\\WTC1-V2.2-12w-A1-DIV24-2022.03.11 cell1 002.axgd"
    ## SPON
    ##ROOTPATH="D:\\data-yves\\labo\\devel\\intrinsic\\samples\\yukti&clara\\WTC1-V2.2-12w-A1-DIV24-2022.03.11-Cell1\\WTC1-V2.2-12w-A1-DIV24-2022.03.11 cell1 005.axgd"
    ##ZAP
    ##ROOTPATH="D:\\data-yves\\labo\\devel\\intrinsic\\samples\\lianglin\\testfiles_1\\20210215 039.axgd"
    ##merged CCSteps, matlab merge
    #ROOTPATH="D:\\data-yves\\labo\\projects\\Patch-Seq-GADGFP\\Cell_Recordings\\20211008_57n\\20211008_57n.maty"
    ## AHP, pclamp version (increasing steps)
    #ROOTPATH="D:\\data-yves\\labo\\projects\\Patch-Seq-GADGFP\\Cell_Recordings\\20211217_111s\\20211217_111s_0006.abf"
    ## ramp
    #ROOTPATH="D:\\data-yves\\labo\\projects\\Patch-Seq-GADGFP\\Cell_Recordings\\20211215_82n\\20211215_82n_0007.abf"
    ## rheobase
    #ROOTPATH="D:\\data-yves\\labo\\projects\\Patch-Seq-GADGFP\\Cell_Recordings\\20211217_110s\\20211217_110s_0001.abf"
    #ROOTPATH="D:\\data-yves\\labo\\projects\\Patch-Seq-GADGFP\\Cell_Recordings\\20211020_61n\\20211011_61n_0001.abf"
    if len(sys.argv)>1:
        ROOTPATH=sys.argv[1]
    ## do not modify after this point!
    try:ROOTPATH
    except:
        logging.getLogger(__name__).critical("ROOTPATH is not defined.") 
        logging.getLogger(__name__).critical("Either provide path to a valid *.axgx,*.axgd,*.abf file,")
        logging.getLogger(__name__).critical("or edit this file to hard code the value of ROOTPATH in __main__ section.")
        exit(0)
    tics = time.perf_counter()
    logging.getLogger(__name__).setLevel(20)
    process(Path(ROOTPATH).resolve())
    logging.getLogger(__name__).info(f"Completed analysis of {filecount} files in {time.perf_counter()-tics} seconds")

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

import logging,time,fnmatch, pprint,re,sys
from pathlib import Path
import neo
import numpy as np
import quantities as pq
import pandas as pd

import scipy
from scipy.signal import butter, lfilter, freqz

def neo_idx(cls,t):
    return round(t*cls._sample_rate)

def neo_volts(cls, start=None, stop=None):
    if not cls.units in [1.0*pq.V,pq.mV,pq.uV]:
        raise NotImplementedError("Don't know how to convert this signal to Volts")
    return neo_array(cls,start,stop,pq.V)

def neo_millivolts(cls, start=None, stop=None):
    if not cls.units in [1.0*pq.V,pq.mV,pq.uV]:
        raise NotImplementedError("Don't know how to convert this signal to Volts")
    return neo_array(cls,start,stop,pq.mV)

def neo_microvolts(cls, start=None, stop=None):
    if not cls.units in [1.0*pq.V,pq.mV,pq.uV]:
        raise NotImplementedError("Don't know how to convert this signal to Volts")
    return neo_array(cls,start,stop,pq.uV)

def neo_amp(cls, start=None, stop=None):
    if not cls.units in [1.0*pq.A,pq.mA,pq.uA,pq.nA,pq.pA]:
        raise NotImplementedError("Don't know how to convert this signal to Volts")
    return neo_array(cls,start,stop,pq.A)

def neo_milliamp(cls, start=None, stop=None):
    if not cls.units in [1.0*pq.A,pq.mA,pq.uA,pq.nA,pq.pA]:
        raise NotImplementedError("Don't know how to convert this signal to Volts")
    return neo_array(cls,start,stop,pq.mA)

def neo_microamp(cls, start=None, stop=None):
    if not cls.units in [1.0*pq.A,pq.mA,pq.uA,pq.nA,pq.pA]:
        raise NotImplementedError("Don't know how to convert this signal to Volts")
    return neo_array(cls,start,stop,pq.uA)

def neo_nanoamp(cls, start=None, stop=None):
    if not cls.units in [1.0*pq.A,pq.mA,pq.uA,pq.nA,pq.pA]:
        raise NotImplementedError("Don't know how to convert this signal to Volts")
    return neo_array(cls,start,stop,pq.nA)

def neo_picoamp(cls, start=None, stop=None):
    if not cls.units in [1.0*pq.A,pq.mA,pq.uA,pq.nA,pq.pA]:
        raise NotImplementedError("Don't know how to convert this signal to Volts")
    return neo_array(cls,start,stop,pq.pA)

def neo_sec(cls,start=None,stop=None):
    return neo_time_array(cls,start,stop,pq.s)

def neo_millisec(cls,start=None,stop=None):
    return neo_time_array(cls,start,stop,pq.ms)

def neo_array(cls,start,stop,qty):
    if start is None and stop is None:
         return cls.rescale(qty).magnitude.flatten()
    if isinstance(start,float) and isinstance(stop,float):
        return cls[int(round(start*cls._sampling_rate)):int(round(stop*cls._sampling_rate))].rescale(qty).magnitude.flatten()
    elif isinstance(start,int) and isinstance(stop,int):
        return cls[start:stop].rescale(qty).magnitude.flatten()
    elif stop is None and isinstance(start,int):
        return float(cls[start].rescale(qty))
    elif stop is None and isinstance(start,float):
        return float(cls[int(round(start*cls._sampling_rate))].rescale(qty))

def neo_time_array(cls,start,stop,qty):
    if start is None and stop is None:
         return cls.times.rescale(qty).magnitude.flatten()
    if isinstance(start,float) and isinstance(stop,float):
        return cls.times[int(round(start*cls._sampling_rate)):int(round(stop*cls._sampling_rate))].rescale(qty).magnitude.flatten()
    elif isinstance(start,int) and isinstance(stop,int):
        return cls.times[start:stop].rescale(qty).magnitude.flatten()
    elif stop is None and isinstance(start,int):
        return float(cls.times[start].rescale(qty))
    elif stop is None and isinstance(start,float):
        return float(cls.times[int(round(start*cls._sampling_rate))].rescale(qty))

def installmonkey():
    neo.AnalogSignal.idx=neo_idx
    neo.AnalogSignal.V=neo_volts
    neo.AnalogSignal.mV=neo_millivolts
    neo.AnalogSignal.uV=neo_microvolts
    neo.AnalogSignal.A=neo_amp
    neo.AnalogSignal.mA=neo_milliamp
    neo.AnalogSignal.uA=neo_microamp
    neo.AnalogSignal.nA=neo_nanoamp
    neo.AnalogSignal.pA=neo_picoamp
    neo.AnalogSignal.s=neo_sec
    neo.AnalogSignal.ms=neo_millisec

def average(*sigs):
    '''usage:
    signals=[ average(sigs[0],sigs[1],sigs[2]),
              average(sigs[3],sigs[4],sigs[5]),
              average(sigs[6],sigs[7],sigs[8])]
    signals=[ average(sig[3*i],sig[3*i+1],sig[3*i+2]) for i range(in len(signals)//3) ]
    signals=[ average(sig[3*i],sig[3*i+k],sig[3*i+k]) for k in range(2) for i range(in len(signals)//3) ]
    '''
    if len(set([str(s.units) for s in sigs]))!=1:
        print(set([str(s.units) for s in sigs]))
        raise NotImplementedError("Don't know how to average signals with different units")
    if len(set([int(s.sampling_rate) for s in sigs]))!=1:
        raise NotImplementedError("Don't know how to average signals with different sampling rates")
    _avg=np.mean([*sigs],axis=0)
    return neo.AnalogSignal(_avg,sampling_rate=sigs[0].sampling_rate, units=sigs[0].units)

def groupaverage(signals,repeats,policy='framerepeat'):
	assert(len(signals)%repeats==0)
	episodes=len(signals)//repeats
	newsignals=[]
	if policy=='framerepeat':
		for f in range(episodes):
			newsignals.append(average(*[signals[repeats*f+r] for r in range(repeats)]))
	elif policy=='protocolrepeat':
		for f in range(episodes):
			newsignals.append(average(*[signals[repeats*(f+e)] for e in range(episodes)]))
	return newsignals

if __name__=='__main__':
    import matplotlib.pyplot as plt
    installmonkey()
    inpath="D:\\data-yves\\labo\\devel\\intrinsic\\yukti&clara\\WTC1-V2.1-12w-B1-DIV28-2022.03.08-Cell2\\wtc1-v2.1-12w-b1-div28-2022.03.08-cell2 002.axgd"
    inpath="C:\\Users\\ylefeuvre\\Desktop\\example files\\sag\\0220509_4473 cell 1 008.axgd"
    inpath="../../samples/yukti&clara/sag/0220509_4473 cell 1 008.axgd"
    f = neo.io.AxographIO(str(inpath),force_single_segment=True)
    blk = f.read_block(signal_group_mode='split-all')
    '''
    sig = [sig for sig in blk.segments[0].analogsignals ][0] ## if len(sig)>1000 and sig.units in [1.0*pq.V,pq.mV]]
    sig = [sig for sig in blk.segments[0].analogsignals ]
    plt.plot(average(sig[0],sig[2]).magnitude)
    plt.plot(sig[0].magnitude,color='b')
    plt.plot(sig[2].magnitude,color='b')
    plt.show()
    '''
    sigs=blk.segments[0].analogsignals
    #sigs=[average(sigs[3*i],sigs[3*i+1],sigs[3*i+2]) for i in range(len(sigs)//3)]
    sigs=groupaverage(sigs,3,'framerepeat')
    for s in sigs:
        plt.plot(s)
    plt.show()


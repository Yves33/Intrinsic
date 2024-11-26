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

import numpy as np
import neo
import quantities as pq
import numbers
import pathlib,logging,pprint

def Experiment(filename):
    if pathlib.Path(filename).is_file():
        suffix=pathlib.Path(filename).suffix
        if suffix in[".abf"]:
            return ABFexperiment(filename)
        if suffix in[".axgd",".axgx"]:
            return AXGexperiment(filename)
        if suffix in[".maty"]:
            return MATYexperiment(filename)
        #if suffix in[".txt",".ascii"]:
        #    return ASCIIexperiment(filename)

class GENexperiment:
    def __init__(self,filename):
        self.path=filename
        self.name=pathlib.Path(filename).resolve().name
        self.suffix=pathlib.Path(filename).resolve().suffix
        self.signalcount=len(self.blk.segments[0].analogsignals)
        self.sweepcount=len(self.blk.segments)
        self.chancount=len(self.blk.segments[0].analogsignals)
        self.samplecount=len(self.blk.segments[0].analogsignals[0]) ##assumes uniform sampling
        self.sampling_rate=self.blk.segments[0].analogsignals[0].sampling_rate
    
    def signal(self,channel,filter='V'):
        '''returns the list of signals corresponding to one channel. signals are scaled to V or A
           if a filter is provided (V or A), the program will only look with signals with specified units
        '''

        sigs=[]
        for seg in self.blk.segments:
            validsigs=[seg.analogsignals[i] for i in range(len(seg.analogsignals)) if str(seg.analogsignals[i].units).endswith(filter)]
            if len(validsigs):
                sig=validsigs[channel]
            else:
                logging.getLogger(__name__).error(f"No signal with units {filter}")
                return
            #sig=seg.analogsignals[channel]
            sig._t_start=0.0*pq.s
            if sig.units in [pq.V,pq.mV,pq.uV]:
                sig=sig.rescale(pq.V)
            elif sig.units in [pq.A,pq.mA,pq.uA,pq.nA,pq.pA]:
                sig=sig.rescale(pq.A)
            else:
                logging.getLogger(__name__).warning("Unknowmn quantity.Can't rescale")
            sigs.append(sig)
        return sigs

class ABFprotocol:
    def __init__(self,exp):
        if exp.file._axon_info["fFileSignature"]==b'ABF ' and \
           exp.file._axon_info["fFileVersionNumber"]>=1.8:
            self.init_v1(exp)
        else:
            self.init_v2(exp)

    def init_v2(self,exp):
        '''backported from v5 to match v3 protocol description'''
        self.name=str(exp.file._axon_info["sProtocolPath"]).split('/')[-1]
        ## epochtype:enum(step,ramp,pulse,train,biphasic_train,triangle_train,cosine_train).old versions do not have trains
        ## units are pA and samples!
        self.samplecount=len(exp.blk.segments[0].analogsignals[0]) ##assumes uniform sampling
        self.sampling_rate=int(exp.blk.segments[0].analogsignals[0].sampling_rate)
        self.offset_p=np.floor(self.samplecount/64)
        self.offset_t=float(np.floor(self.samplecount/64)/self.sampling_rate)
        self.episode_cnt=exp.file._axon_info['lActualEpisodes']
        self.episode_repeat=exp.file._axon_info['lActualEpisodes']//exp.file._axon_info['protocol']['lEpisodesPerRun']
        self.epochproperties=[k for k in exp.file._axon_info.keys() if "Epoch" in k ]
        '''
        nepochs=len(exp.file._axon_info[self.epochproperties[0]])
        self.epochs=[]
        #print(self.epochproperties)
        for i in range(nepochs):
            self.epochs.append({})
            for k in self.epochproperties:
                self.epochs[-1][k]=exp.file._axon_info[k][i]
        '''
        ## special case handling
        if len(exp.file._axon_info['dictEpochInfoPerDAC'].keys())==0:
            self.epochs=[]
            self.epochproperties=[]
            return
        self.epochproperties=exp.file._axon_info['dictEpochInfoPerDAC'][0]
        nepochs=len(self.epochproperties.keys())
        self.epochs=[]
        for i in range(nepochs):
            self.epochproperties[i]['lEpochInitTrainPeriod']=self.epochproperties[i]['lEpochPulsePeriod']
            self.epochproperties[i]['lEpochInitPulseWidth']=self.epochproperties[i]['lEpochPulseWidth']
            self.epochs.append(self.epochproperties[i])
            #epochs[-1]['lEpochInitTrainPeriod']=epochs[-1]['lEpochPulsePeriod']
            #epochs[-1]['lEpochInitPulseWidth']=epochs[-1]['lEpochPulseWidth']
            #epochs[-1]['lEpochTrainPeriodInc']=0         ## not handled by pClamp / clampex v11
            #epochs[-1]['lEpochPulseWidthInc']=0          ## not handled by pClamp / clampex v11

    def init_v1(self,exp):
        self.name=str(exp.file._axon_info["sProtocolPath"]).split('/')[-1]
        ## epochtype:enum(step,ramp,pulse,train,biphasic_train,triangle_train,cosine_train).old versions do not have trains
        ## units are pA and samples!
        self.samplecount=len(exp.blk.segments[0].analogsignals[0]) ##assumes uniform sampling
        self.sampling_rate=int(exp.blk.segments[0].analogsignals[0].sampling_rate)
        self.offset_p=np.floor(self.samplecount/64)
        self.offset_t=float(np.floor(self.samplecount/64)/self.sampling_rate)
        self.episode_cnt=exp.file._axon_info['lActualEpisodes']
        self.episode_repeat=exp.file._axon_info['lActualEpisodes']//exp.file._axon_info['lEpisodesPerRun']
        self.epochproperties=[k for k in exp.file._axon_info.keys() if "Epoch" in k ]
        nepochs=len(exp.file._axon_info[self.epochproperties[0]])
        self.epochs=[]
        #print(self.epochproperties)
        for i in range(nepochs):
            self.epochs.append({})
            for k in self.epochproperties:
                self.epochs[-1][k]=exp.file._axon_info[k][i]
    
    def asdict(self):
        return {k:getattr(self,k) for k in dir(self) if not k.startswith('__')}
    
    def ascurrentsteps(self):
        start=self.offset_t
        steps=[]
        for e in range(self.episode_cnt):
            step={}
            step['start']=(self.offset_p+self.epochs[0]['lEpochInitDuration']+e*self.epochs[0]['lEpochDurationInc'])/self.sampling_rate
            step['dur']=(self.epochs[1]['lEpochInitDuration']+e*self.epochs[1]['lEpochDurationInc'])/self.sampling_rate
            step['stop']=step['start']+step['dur']
            step['lvl']=round((self.epochs[1]['fEpochInitLevel']+e*self.epochs[1]['fEpochLevelInc']))
            steps.append(step)
        return {'steps':steps}
  
class ABFexperiment(GENexperiment):
    def __init__(self,filename,**kwargs):
        self.file=neo.io.AxonIO(str(filename))
        self.blk=self.file.read_block(signal_group_mode='split-all')
        #self.protocol=ABFprotocol(self,exp)
        #super(ABFexperiment,self).__init__(filename)
        super(ABFexperiment,self).__init__(filename)
        self.protocol=ABFprotocol(self)

def is_num(s):
    if (s.find('-') <= 0) and s.replace('-', '', 1).isdigit():
        if (s.count('-') == 0):
            s_type = 'Positive Integer'
        else:
            s_type = 'Negative Integer'
    elif (s.find('-') <= 0) and (s.count('.') < 2) and \
         (s.replace('-', '', 1).replace('.', '', 1).isdigit()):
        if (s.count('-') == 0):
            s_type = 'Positive Float'
        else:
            s_type = 'Negative Float'
    else:
        s_type = "Not alphanumeric!"
        return False
    return True

def num(x):
    try:
        return float(x) if '.' in x else int(x)
    except:
        return x

class AXGprotocol:
    def __init__(self, exp):
        ##parses a prototol from experiment
        ## protocol pulse fields. some remain unknown...
        ## not that sure for gap_inc and average, but as they're not used by current protocols...
        fields=['average','wavrepeat','cnt','start','start_inc','dur','dur_inc',7,'gap','gap_inc',10,'lvl','lvl_inc',13,14]
        notes=exp.blk.annotations['notes'].split('\n')
        self.name=exp.file.info["comment"].split(':')[1].rstrip().lstrip()
        self.pulses=[] ## create new list of pulses
        '''for n in notes:
            ## protocols description may vary...
            if n.startswith("Start an episode every"): self.episode_interval=[float(x) for x in n.split() if  is_num(x)][0]
            elif n.startswith("Pause after waveform series"): self.episode_gap=[float(x) for x in n.split() if is_num(x)][0]
            elif n.startswith("Repeat protocol"): self.episode_repeat=[int(x) for x in n.split() if is_num(x)][0]
            ##['Repeat each waveform, then step to next waveform']
            elif n.startswith("DAC Holding Levels"):dac_hold=[int(x) for x in n.split('\t') if is_num(x)]
            elif n.startswith("Episodes"):self.episode_cnt=[int(x) for x in n.split(' ') if is_num(x)][0]
            elif n.startswith("Pulses") and '#' not in n:self.pulse_cnt=[int(x) for x in n.split(' ') if is_num(x)][0]
            elif n.startswith("Pulse #") : self.pulses.append({'type':'pulse'}) ## create new list of pulses
            elif n.startswith("Train #") : self.pulses.append({'type':'train'}) ## create new list of pulses
            ## units are ms and nA in AF protocols
            elif len(n.split('\t'))==16:self.pulses[-1].update({k:num(v) for k,v in zip(fields,n.split('\t'))})
        '''
        ## new parser. not sure if it is more reliable!
        currentpulse=0
        for n in notes:
            ## protocols description may vary...
            if n.startswith("Start an episode every"): self.episode_interval=[float(x) for x in n.split() if  is_num(x)][0]
            elif n.startswith("Pause after waveform series"): self.episode_gap=[float(x) for x in n.split() if is_num(x)][0]
            elif n.startswith("Repeat protocol"): self.episode_repeat=[int(x) for x in n.split() if is_num(x)][0]
            ##['Repeat each waveform, then step to next waveform']
            elif n.startswith("DAC Holding Levels"):self.dac_hold=[int(x) for x in n.split('\t') if is_num(x)]
            elif n.startswith("Episodes"):self.episode_cnt=[int(x) for x in n.split(' ') if is_num(x)][0]
            elif n.startswith("Pulses") and '#' not in n:
                self.pulse_cnt=[int(x) for x in n.split(' ') if is_num(x)][0]
                for p in range(self.pulse_cnt):
                    self.pulses.append({'type':'pulse'})
            elif n.startswith("Pulse #") : self.pulses[currentpulse].update({'type':'pulse'}) ## create new list of pulses
            elif n.startswith("Train #") : self.pulses[currentpulse].update({'type':'train'}) ## create new list of pulses
            elif len(n.split('\t'))==16:
                self.pulses[currentpulse].update({k:num(v) for k,v in zip(fields,n.split('\t'))})
                currentpulse+=1
        self.parsepulsetables(notes) ## as a replacement for xx inc, axograph may define pulse tables that define the values of amplitude,onset, width and interpulse for each episode!

    def parsepulsetables(self, notes):
        self.pulsetables={'Amplitude':[],'Onset':[],'Width':[],'Inter-Pulse':[]}
        idx=0
        target=''
        idx=0
        while idx<len(notes):
            n=notes[idx]
            if 'Table Entries' in n:
                l=int(n.split(' ')[-1])
                target=n.split(' ')[0]
            elif target!='':
                try:
                    self.pulsetables[target].append(float(n))
                except:
                    target=''
            idx+=1
        
    def asdict(self):
        return {k:getattr(self,k) for k in dir(self) if not k.startswith('__')}
    
    def ascurrentsteps(self):
        steps=[]
        for e in range(self.episode_cnt):
            for r in range(self.episode_repeat):
                step={}
                step['start']=(self.pulses[0]['start']+e*self.pulses[0]['start_inc'] ) / 1000
                step['dur']=(self.pulses[0]['dur']+e*self.pulses[0]['dur_inc'] ) / 1000
                step['stop']=(self.pulses[0]['dur']+e*self.pulses[0]['dur_inc']+self.pulses[0]['start']+e*self.pulses[0]['start_inc']  ) / 1000
                step['lvl']=round((self.pulses[0]['lvl']+e*self.pulses[0]['lvl_inc'] ) * 1000)
                steps.append(step)
        return {'steps':steps}
        #exp.protocol.assteps()['steps'][0]['start']
        #exp.protocol.assteps()['steps'][0]['stop']
        #[s['lvl'] for i in exp.protocol.assteps()['steps'] ]

class AXGexperiment(GENexperiment):
    def __init__(self,filename):
        self.file=neo.io.AxographIO(str(filename))
        self.blk=self.file.read_block(signal_group_mode='split-all')
        self.protocol=AXGprotocol(self)
        super(AXGexperiment,self).__init__(filename)

class MATYprotocol:
    def __init__(self,exp):
        for k,v in exp.blk.annotations.items():
            setattr(self,k,v)
            self.name=self.protocolname
    
    def asdict(self):
        return {k:getattr(self,k) for k in dir(self) if not k.startswith('__')}

    def ascurrentsteps(self):
        steps=[]
        for e in range(self.episode_cnt):
            step={}
            step['start']=self.start
            step['dur']=self.dur
            step['stop']=self.start+self.dur
            step['lvl']=self.steps[e]
            steps.append(step)
        return {'steps':steps}

class MATYexperiment(GENexperiment):
    """only used for merged ccsteps files"""
    def __init__(self,filename):
        self.file=neo.io.NeoMatlabIO(str(filename))
        self.blk=self.file.read_block()
        self.protocol=MATYprotocol(self)
        super(MATYexperiment,self).__init__(filename)

if __name__=='__main__':
    ROOT="../yukti&clara/"
    ## time constant
    PATH="WTC1-V2.2-12w-A1-DIV24-2022.03.11-Cell4\WTC1-V2.2-12w-A1-DIV24-2022.03.11 cell4 004.axgd"
    ##resistance
    PATH="WTC1-V2.2-12w-A1-DIV24-2022.03.11-Cell4\WTC1-V2.2-12w-A1-DIV24-2022.03.11 cell4 005.axgd"
    ##AHP_MED
    PATH="WTC1-V2.2-12w-A1-DIV24-2022.03.11-Cell2\WTC1-V2.2-12w-A1-DIV24-2022.03.11 cell2 009.axgd"
    ##AHP_SLOW
    #PATH="WTC1-V2.2-12w-A1-DIV24-2022.03.11-Cell2\WTC1-V2.2-12w-A1-DIV24-2022.03.11 cell2 011.axgd"
    ## IV
    #PATH="WTC1-V2.2-12w-A1-DIV24-2022.03.11-Cell2\WTC1-V2.2-12w-A1-DIV24-2022.03.11 cell2 001.axgd"
    PATH="WTC1-V2.2-12w-A1-DIV24-2022.03.11-Cell1\WTC1-V2.2-12w-A1-DIV24-2022.03.11 cell1 002.axgd"
    ## SPON
    #PATH="WTC1-V2.2-12w-A1-DIV24-2022.03.11-Cell1\WTC1-V2.2-12w-A1-DIV24-2022.03.11 cell1 005.axgd"
    ##ZAP
    #ROOT="../lianglin/"
    #PATH=r"testfiles_1\20210215 039.axgd"
    ##ROOT="./"
    ###PATH="test.mat"
    #ROOT="../../projects/Patch-Seq-GADGFP/Cell_Recordings/"
    #PATH="20211215_85n\\20211215_85n_0003.abf"

    ROOTPATH=ROOT+PATH.replace('\\','/')
    #ROOTPATH="D:\\data-yves\\labo\\projects\\Patch-Seq-GADGFP\\Cell_Recordings\\20211215_85n\\20211215_85n_0002.abf"
    #ROOTPATH="D:\\data-yves\\labo\\projects\\Patch-Seq-GADGFP\\Cell_Recordings\\20211008_57n\\20211008_57n.maty"
    ## do not modify after this point!
    #ROOTPATH="D:\\data-yves\\labo\\projects\\Patch-Seq-GADGFP\\Cell_Recordings\\20211215_85n\\20211215_85n_0002.abf"
    ROOTPATH="D:\\data-yves\\labo\projects\\Patch-Seq-GADGFP\\Cell_Recordings\\20190117_07s\\20190117_07s_fit.txt"
    ROOTPATH="C:\\Users\\ylefeuvre\\Desktop\\example files\\sag\\0220509_4473 cell 1 008.axgd"
    ROOTPATH="/home/bigdata/Documents/intrinsic-3.2.6-20230208_src/13.02.18 000.axgd"
    myexp=Experiment(pathlib.Path(ROOTPATH).resolve())
    #pprint.pprint(myexp.protocol.ascurrentsteps())
    import matplotlib.pyplot as plt
    plt.plot(myexp.signal(0)[1].times, myexp.signal(0)[1].magnitude)
    plt.show()




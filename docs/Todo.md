TODO :
=====================
**implementation**
for ivframe, the current is read within ivframe constructor, whereas for rheobase or sagratio, the current is passed to protocol constructor.
this should be homogenized for all all protocols that require pulse intensity (rheobase, resistance, iv, sagratio )
+ Current should be renamed to command
+ All protocols should have a command (list) value in protocol, with same length as sigs (could be [None]*30)
+ command can be a list of float, int, or AnalogSignals, with same length as sigs
protocolo(sigs=, command=, interactive=True, **kwargs)
frame(sig,command,index,**kwargs)

**users**
+ it would be a **good** idea to homogenize ptotocol names, and have some kind of consistent naming
something like:
CC_IVCURVE(version)_base(-200pA)_step(+20pA)_dur(2000ms).[pro,axgx]
CC_AHP(version)_AP(xx)_freq(yyHz).[pro,axgx]
CC_RHEOBASE(version)_base(+0pA)_step(+5pA)_dur(50ms).[pro,axgx]
CC_RESISTANCE(version)_base(-50pA)_step(+0pA).[pro,axgx]
CC_SAG(version)_base(+0pA)_step(-100pA).[pro,axgx]
CC_IMPEDENCE(version)_start(+xxHz)_end(+yyHz).[pro,axgx]
VC_RAMP(version)_base(-40pA)_ramp(-80pA)_dur(1000ms).[pro,axgx]
VC_RAMPSYM(version)_base(-40pA)_ramp(-80pA)_dur(1000ms).[pro,axgx]
VC_PPR(version)_gap(+20ms).[pro,axgx]
VC_ACTIVATION(version)_base(-60mV)_step(+10mV)_duration(100ms)_prepulse(xxmV).[pro,axgx]
VC_INACTIVATION(version)_base(-60mV)_step(+10mV)_duration(100ms)_postpulse(xxmV).[pro,axgx]
VC_SPON(version)_vhold(+0mV)_dur(3min).[pro,axgx]
CC_SPON(version)_ihold(+0pA)dur(3min).[pro,axgx]

+ for backward compatibility, one could maintain a translation dict to translate old protocols to new ones

+ scripts to generate IVcurves from panda dataframes (done)
+ scripts to parse @itsq files (eg average spikes pp, generate sagratio=f(steady_state) curves, ...) (done)

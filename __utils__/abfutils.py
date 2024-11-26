"""
basic utilities specific to abf files...
"""
import numpy as np
import neo
import numpy as np
import quantities as pq

def merge2matlab(*args,**kwargs):
    current_steps=list(range(-95,100,5))
    mergefiles=[*args]
    mergefilename=str(args[0]).replace(".abf",".maty")
    allframes={c:None for c in current_steps}
    for f in sorted(mergefiles):
        ## for each file
        f = neo.io.AxonIO(str(f))
        if "CCSteps" not in str(f._axon_info["sProtocolPath"]):
            continue
        blk = f.read_block(signal_group_mode='split-all')
        numsamples=len(blk.segments[0].analogsignals[0])
        sr=blk.segments[0].analogsignals[0]._sampling_rate
        EXTRATIME=float(np.floor(numsamples/64)/sr) ## axon files add an extra time
        lvl=int (f._axon_info["fEpochInitLevel"][1])                                    ## epoch start level
        lvl_inc=int(f._axon_info["fEpochLevelInc"][1]) 
        start=(f._axon_info["lEpochInitDuration"][0])/f._sampling_rate
        stop=(f._axon_info["lEpochInitDuration"][0]+f._axon_info["lEpochInitDuration"][1])/f._sampling_rate
        start+=EXTRATIME
        stop+=EXTRATIME
        for e,segment in enumerate(blk.segments):
            cstep=int(lvl+e*lvl_inc)
            if cstep in current_steps and allframes[cstep] is None: ## if  
                ## keep only first signal in segment whith units V or mV, rescale everything to V and s, and make sure signal starts at 0s
                voltage=[sig for sig in segment.analogsignals if len(sig)>1000 and sig.units in [1.0*pq.V,pq.mV]][0]
                voltage.rescale(pq.V)
                voltage._t_start=0.0*pq.s
                try:
                    current=[sig for sig in segment.analogsignals if len(sig)>1000 and sig.units in [1.0*pq.A,pq.mA,pq.uA,pq.nA,pq.pA]][0]
                    current.rescale(pq.A)
                    current._t_start=0.0*pq.s
                except:
                    print("could not find any current!!")
                allframes[cstep]=(voltage.rescale(pq.V),current.rescale(pq.A))
    allframes={k:v for k,v in allframes.items() if not v is None}
    allcurrents=list(allframes.keys())
    print(allcurrents)
    sigs=list(allframes.values())
    
    blk=neo.Block('Merged current steps protocol')
    print(start,stop,stop-start,allcurrents[0],allcurrents[1]-allcurrents[0])
    blk.annotate( protocolname="IV-curve",
                  episode_cnt=len(allcurrents),
                  episode_repeat=1,
                  start=start,
                  stop=stop,
                  dur=stop-start,
                  lvl=allcurrents[0],
                  lvl_inc=allcurrents[1]-allcurrents[0],
                  steps=allcurrents)
    for k,v in allframes.items():
        seg=neo.Segment('')
        blk.segments.append(seg)
        seg.analogsignals.append(v[0])
        seg.analogsignals.append(v[1])
    #p_out = neo.io.PickleIO(filename="./test.pickle")
    #p_out.write_block(blk)
    m_out = neo.io.NeoMatlabIO(filename=mergefilename)
    m_out.write_block(blk)

if __name__ == '__main__':
    import wx
    import pathlib
    #merge2matlab(pathlib.Path("D:\\data-yves\\labo\\projects\\Patch-Seq-GADGFP\\Cell_Recordings\\20211008_57n\\20211008_57n.abfmerge"))
    #f=neo.io.NeoMatlabIO(filename="D:\\data-yves\\labo\\projects\\Patch-Seq-GADGFP\\Cell_Recordings\\20211008_57n\\20211008_57n.maty")
    #block=f.read_block()
    #print("Done")

    class FileDrop(wx.FileDropTarget):
        def __init__(self, window):
            wx.FileDropTarget.__init__(self)
            self.window = window

        def OnDropFiles(self, x, y, filenames):
            merge2matlab(*filenames)
            return True

    class Example(wx.Frame):
        def __init__(self, *args, **kw):
            super(Example, self).__init__(*args, **kw)
            self.InitUI()

        def InitUI(self):
            self.text = wx.TextCtrl(self, style = wx.TE_MULTILINE)
            dt = FileDrop(self.text)
            self.text.SetDropTarget(dt)
            self.SetTitle('Drop abf files to merge them')
            self.Centre()

    app = wx.App()
    ex = Example(None)
    ex.Show()
    app.MainLoop()

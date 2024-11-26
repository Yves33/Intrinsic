from pathlib import Path
import json

'''
How does it work:
The script will look *recursively* for all '*.itsq' files in srcpath
if the itsq file is an IV protocol,
- it parses the experiment name looking at parent folder name 
- it looks for a frame with more than 3 evoked spikes (injected current positive and correct timing)
- it computes the ratio between the half width of the 3rd spike and the first one
- it prints the results to stdout

if wxpython is installed, the program will show a simple window where you should drop any folder containing *.itsq files
'''

def scan(srcpath):
    results={}
    if Path(srcpath).is_file() and Path(srcpath).suffix=='.itsq':
        results.update(apw_ratio(Path(srcpath)))
    else:
        for inpath in Path(srcpath).glob('**/*.itsq'):
            results.update(apw_ratio(inpath))
    return results

def apw_ratio(inpath):
    results={}
    folder=inpath.parent.parent.name                                        ## gets the name of cell ()
    ## we may have some failures... with jsonpickle
    ## as we are not trying to reparse signals, one can just load with normal json
    try:
        protocol=json.loads(open(str(inpath)).read())                           ## open file
    except:
        return{folder:"ERR_CANT_PARSE ITSQ"}
    if protocol["py/object"]=="intrinsic.ivprotocol":                       ## if file is an intrinsic protocol
        frames=[f for f in protocol["frames"] if len(f["evokedspikes"])>2]  ## build a list of frames with 3 spikes or more
        if len(frames):                                                     ## if the list is not empty
            spikes=[s for s in frames[0]["spikes"] if s["evoked"]]          ## builds a list of evoked spikes for first frame with a least 3 spikes 
            try:
                apw_ratio=spikes[2]["halfwidth"]/spikes[0]["halfwidth"]     ## computes ratio
                return{folder:apw_ratio}                                  ## stores in dictionnary
            except:
                return{folder:"ERR_INCOMPLETE_SPIKES"}
        else:
            return{folder:"ERR_NO_SUITABLE_FRAME"}
    return results

if __name__=='__main__':
    try:
        import wx
        class FileDrop(wx.FileDropTarget):
            def __init__(self, window):
                wx.FileDropTarget.__init__(self)
                self.window = window
            def OnDropFiles(self, x, y, filenames):
                r=scan(*filenames)
                self.window.SetValue('')
                for k,v in r.items():
                    self.window.AppendText(f"{k}\t{v}\n" )
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
    except:
        srcpath="../../samples/yukti&clara"
        scan(srcpath)

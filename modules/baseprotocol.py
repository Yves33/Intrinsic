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

import os
from pathlib import Path

from collections.abc import Iterable
import pickle,json
import jsonpickle
import jsonpickle.ext.numpy as jsonpickle_numpy
import jsonpicklehandlers
from functools import partial

import matplotlib
import matplotlib.pyplot as plt
from mpl_interaction import PanAndZoom
from mpl_toolbutton import TriggerBtn,ToggleBtn
from mpl_draggable import draggable_line

######################################################################################
## baseframe and baseprotocol
## ancestors to any **frame and **procotol
#######################################################################################
def once(method):
    def inner(ref):
        if len(ref._axes())==0:
            return method(ref)
    return inner

class BaseFrame:
    def __init__(self,idx,parent):
        self.idx=idx
        self.parent=parent
        self.enabled=True
        self.process() ## only exists in derived class

    def activate(self):
        ## to be called when the frame becomes current.
        pass

    def deactivate(self):
        ## to be called when the frame becomes current. currently unused
        pass

    def _cursor(self,ax,dir,value,cb):
        ## keep a reference to created cursor in figure, otherwise the cursor object disappears (while the line is still present on graph!)
        ## TODO super trivial, but requires testing...
        ## cursors should be attached to protocol, not to fig()
        ## _cursor should return the draggable line (return self.parent.cursors[-1])
        if isinstance(ax,Iterable):
            self.parent.cursors.append(draggable_line(ax,dir, value, cb))
            return self.parent.cursors[-1]
        else:
            self.parent.cursors.append(draggable_line([ax],dir, value, cb))
            return self.parent.cursors[-1]

    def _get_cursor(self,x):
        return self.parent.cursors[x]

    def _clf(self,ids):
        for ax in self._axes():
            self._cla(ax,ids)
    
    def _cla(self,ax,ids):
        for l in ax.lines[::-1]:
            if l.get_gid() in ids:
                try:
                    l.remove()
                    del l
                except:
                    pass

    def _fig(self):
        return self.parent._fig()

    def _axes(self,idx=-1):
        return self.parent._axes(idx)
import wx
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import (
    FigureCanvasWxAgg as FigureCanvas,
    NavigationToolbar2WxAgg
    )
class ModalFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, style=wx.DEFAULT_FRAME_STYLE|wx.STAY_ON_TOP)
        self.fig = Figure((1,1))
        #plt.gcf=lambda:self.fig ## awfull hack! (really awfull)
        super().__init__(parent, -1)
        self.canvas = FigureCanvas(self, -1, self.fig)
        self.toolbar = NavigationToolbar2WxAgg(self.canvas)  # matplotlib toolbar
        self.toolbar.Realize()

        # Now put all into a sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        # Best to allow the toolbar to resize!
        sizer.Add(self.toolbar, 0, wx.EXPAND)
        # This way of adding to sizer allows resizing
        sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()
        self.Bind(wx.EVT_CLOSE, self.onClose) # (Allows main window close to work)

    def onClose(self, event):
        self.MakeModal(False) # (Re-enables parent window)
        self.eventLoop.Exit()
        self.Destroy() # (Closes window without recursion errors)

    def ShowModal(self):
        self.MakeModal(True) # (Explicit call to MakeModal)
        self.Show()
        self.eventLoop = wx.EventLoop()
        self.eventLoop.Run()

class BaseProtocol:
    def __init__(self,interactive,fig=None,pzwheelonly=True):
        self.f=0
        self.cursors=[]
        if fig is None:
            self.fig=plt.gcf()
        else:
            self.fig=fig
        if interactive:
            pan_zoom = PanAndZoom(self._fig(),pzwheelonly)
            iconpath=Path(os.getcwd()).resolve()
            #iconpath=Path(__file__).parent.resolve()
            if len(self.frames)>1:
                fwdbtn=TriggerBtn(self._fig(),"prev",'alt+p',str(iconpath/'resources/fa-backward-solid.png'),'Jump to previous frame',self.prevframe)
                trashbtn=ToggleBtn(self._fig(),"disable",'alt+d',str(iconpath/'resources/fa-trash-solid.png'),'Disable/enable this frame',self.toggleframe)
                bwdbtn=TriggerBtn(self._fig(),"next",'alt+n',str(iconpath/'resources/fa-forward-solid.png'),'Jump to next frame',self.nextframe)
                allbtn=TriggerBtn(self._fig(),"all",'alt+a',str(iconpath/'resources/fa-redo-solid.png'),'Apply parameters to all frames',self.processall)
            else:
                trashbtn=ToggleBtn(self._fig(),"disable",'alt+d',str(iconpath/'resources/fa-trash-solid.png'),'Disable/enable this frame',self.toggleframe)
            self.frames[self.f].draw()
            self._fig().canvas.draw()
            ## quite complex situation here:
            ## if fig is None, it is created through the pyplot module, 
            ## we have to show it using plt.show()
            ## if backend is wx and we're already running an event loop through the app,
            ## matplotlib will run in non blocking mode and will not start another eventloop.
            ## we can however force starting an event loop immediately using one of the next lines
            #plt.show();plt.gcf().canvas.start_event_loop()
            #plt.pause(-1)
            #plt.ginput(n=-1,timeout=-1,show_clicks=False)
            if not fig:
                if 'wx' in str(matplotlib.get_backend()).lower():
                    import wx
                    if wx.App.IsMainLoopRunning():
                        #plt.pause(-1)
                        #plt.ion()
                        #plt.ginput(n=-1,timeout=200000,show_clicks=False)
                        plt.show(block=False);plt.gcf().canvas.start_event_loop()
                    else:
                        plt.show()
                else:
                    plt.show()

    def _fig(self):
        return self.fig

    def _axes(self,idx=-1):
        if idx==-1:
            return self.fig.get_axes()
        else:
            return self.fig.get_axes()[idx]

    def currentframe(self):
        return self.frames[self.f]

    def nextframe(self,*args,**kwargs):
        self.frames[self.f].deactivate()
        self.f=max(0, min(self.f+1, len(self.frames)-1)) ## quick clamp
        self.frames[self.f].activate()
        self.frames[self.f].draw()
        self.colorize()
        self._fig().canvas.draw()

    def prevframe(self,*args,**kwargs):
        self.frames[self.f].deactivate()
        self.f=max(0, min(self.f-1, len(self.frames)-1)) ## quick clamp
        self.frames[self.f].activate()
        self.frames[self.f].draw()
        self.colorize()
        self._fig().canvas.draw()

    def toggleframe(self,*args,**kwargs):
        self.frames[self.f].enabled=not self.frames[self.f].enabled
        self.colorize()
        self._fig().canvas.draw()

    def colorize(self):
        self._fig().patch.set_facecolor('white' if self.frames[self.f].enabled else 'silver')
        for ax in self._axes():
            ax.set_facecolor('white' if self.frames[self.f].enabled else 'silver')

    def process(self, bitmask=0xFFFF):
        self.frames[self.f].process(bitmask)

    def processall(self,*args,**kwargs):
        for f in self.frames:
            f.process(0xFFFF)
        self.draw(False)

    def draw(self,drawall=True):
        self.frames[self.f].draw(drawall)

    def savedata(self,basefile,protocolname):
        parentdir=Path(basefile).resolve().parent
        stem=Path(basefile).resolve().stem
        if not os.path.exists(parentdir/"@itsq"):
            os.mkdir(parentdir/"@itsq")
        filename=parentdir/f"@itsq/{stem}.itsq"
        # since cursors are now bound to protocol, and theyr reference axes() which references fig(), jsonpickle fails
        # we can just transform cursors to tupple (orientation/value)
        self.cursors=[(c.o,c.getpos()) for c in self.cursors]
        del self.fig
        with open(filename, 'w') as outfile:
            self.protocolname=protocolname
            outfile.write(json.dumps(json.loads(jsonpickle.encode(self,unpicklable=True)), indent=4))
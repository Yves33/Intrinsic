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

import matplotlib.pyplot as plt
import matplotlib.lines as lines

class draggable_line:
    cursorpositions=[]
    def __init__(self, axes, kind, XorY, callback=None,colors=["black","red"],dashes=[1,1],blit=True):
        ## could add a spancolor that would go from cursor(n) to cursor(n+1)
        self.idx=len(draggable_line.cursorpositions)     ## index in the array of cursor positions
        self.cursorpositions.append(XorY)                ## mark position
        self.callback=callback                           ## callback to be called when cursor is released callback(idx,action,positions)
        self.axes = axes
        self.o = kind
        self.XorY = XorY
        self.colors=colors
        self.lines=[]
        self.dashes=dashes
        for ax in self.axes:
            if kind == "h":
                self.lines.append(ax.axhline(XorY,picker=2,color=self.colors[0],dashes=dashes,gid='hcursors'))
            elif kind == "v":
                self.lines.append(ax.axvline(XorY,picker=2,color=self.colors[0],dashes=dashes,gid='vcursors'))
            ax.get_figure().canvas.draw_idle()
            if blit:
                ax.get_figure().canvas.mpl_connect('pick_event', self.clickonline_blit)
            else:
                ax.get_figure().canvas.mpl_connect('pick_event', self.clickonline_draw)
        self.bg=None
        self.fig=self.axes[0].get_figure()

    def clickonline_blit(self, event):
        if event.mouseevent.button!=1:
            return
        clicks=[event.artist == l for l in self.lines]
        if any(clicks):
            index=clicks.index(True)
            self.follower = self.axes[index].get_figure().canvas.mpl_connect("motion_notify_event", self.followmouse_blit)
            self.releaser = self.axes[index].get_figure().canvas.mpl_connect("button_press_event", self.releaseonclick)
            
            for e in range(len(self.lines)):
                self.lines[e].set_linestyle('None')
            self.axes[0].get_figure().canvas.draw()
            self.bg = self.fig.canvas.copy_from_bbox(self.fig.bbox)

            for e in range(len(self.lines)):
                self.lines[e].set_linestyle('-')
                self.lines[e].set_dashes(self.dashes)
                self.lines[e].set_color(self.colors[1])
                self.axes[e].draw_artist(self.lines[e])
                self.axes[e].get_figure().canvas.draw_idle()

    def clickonline_draw(self, event):
        clicks=[event.artist == l for l in self.lines]
        if any(clicks):
            index=clicks.index(True)
            self.follower = self.axes[index].get_figure().canvas.mpl_connect("motion_notify_event", self.followmouse_draw)
            self.releaser = self.axes[index].get_figure().canvas.mpl_connect("button_press_event", self.releaseonclick)
            for e in range(len(self.lines)):
                self.lines[e].set_color(self.colors[1])
                self.axes[e].get_figure().canvas.draw_idle()

    def setpos(self,XorY):
        if self.o == "h":
            for e in range(len(self.lines)):
                self.lines[e].set_ydata([XorY, XorY])
            self.axes[0].get_figure().canvas.draw_idle()    ## drawing the figure canvas will draw all the lines!
            self.XorY = self.lines[0].get_ydata()[0]        ## need only one value (all lines share the same value)
        else:
            for e in range(len(self.lines)):
                self.lines[e].set_xdata([XorY,XorY])
            self.axes[0].get_figure().canvas.draw_idle()
            self.XorY = self.lines[0].get_xdata()[0]
        self.cursorpositions[self.idx]=self.XorY

    def getpos(self):
        if self.o == "h":
            self.XorY = self.lines[0].get_ydata()[0]        ## need only one value (all lines share the same value)
        else:
            self.XorY = self.lines[0].get_xdata()[0]
        return self.XorY

    def followmouse_blit(self, event):
        self.fig.canvas.restore_region(self.bg)
        if self.o == "h":
            for e in range(len(self.lines)):
                self.lines[e].set_ydata([event.ydata, event.ydata])
                self.axes[e].draw_artist(self.lines[e])
            self.fig.canvas.blit(self.fig.bbox)
            self.XorY = self.lines[0].get_ydata()[0]        ## need only one value (all lines share the same value)
        else:
            for e in range(len(self.lines)):
                self.lines[e].set_xdata([event.xdata, event.xdata])
                self.axes[e].draw_artist(self.lines[e])
            self.fig.canvas.blit(self.fig.bbox)
            self.XorY = self.lines[0].get_xdata()[0]
        self.cursorpositions[self.idx]=self.XorY
        #if self.callback!=None:
        #    self.callback(self.idx,'motion',self.neighbours)

    def followmouse_draw(self, event):
        if self.o == "h":
            for e in range(len(self.lines)):
                self.lines[e].set_ydata([event.ydata, event.ydata])
            self.axes[0].get_figure().canvas.draw_idle()    ## drawing the figure canvas will draw all the lines!
            self.XorY = self.lines[0].get_ydata()[0]        ## need only one value (all lines share the same value)
        else:
            for e in range(len(self.lines)):
                self.lines[e].set_xdata([event.xdata, event.xdata])
            self.axes[0].get_figure().canvas.draw_idle()
            self.XorY = self.lines[0].get_xdata()[0]
        self.cursorpositions[self.idx]=self.XorY
        #if self.callback!=None:
        #    self.callback(self.idx,'motion',self.neighbours)

    def releaseonclick(self, event):
        self.fig.canvas.blit(self.fig.bbox)
        if self.o == "h":
            self.XorY = self.lines[0].get_ydata()[0]
        else:
            self.XorY = self.lines[0].get_xdata()[0]
        self.cursorpositions[self.idx]=self.XorY
        for e in range(len(self.lines)):
            self.lines[e].set_color(self.colors[0])
            self.axes[e].get_figure().canvas.mpl_disconnect(self.releaser)
            self.axes[e].get_figure().canvas.mpl_disconnect(self.follower)
        self.axes[0].get_figure().canvas.draw_idle()
        if self.callback!=None:
            #self.callback(self.idx,'release',self.neighbours)
            self.callback(self.XorY)
        
        
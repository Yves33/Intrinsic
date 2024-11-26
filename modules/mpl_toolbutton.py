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

import logging
import numpy
import matplotlib.pyplot as _plt
_plt.rcParams['toolbar'] = 'toolmanager'
from matplotlib.backend_tools import ToolBase, ToolToggleBase
import random,string,functools

def TrigButtonFactory(btnkey,btnicon,btndesc,btncb=None, BaseClass=ToolBase):
    '''generates a new class with random name'''
    def __init__(self, *args,**kwargs):
        BaseClass.__init__(self,*args[:2],**kwargs)
    klass = type(''.join(random.choice(string.ascii_lowercase) for i in range(10)), 
                (BaseClass,),{"__init__": __init__,
                                "default_keymap":btnkey,
                                "description":btndesc,
                                "image":btnicon,
                                "trigger":btncb
                                })
    return klass

def ToggleButtonFactory(btnkey,btnicon,btndesc,btncb=None, BaseClass=ToolToggleBase):
    '''generates a new class with random name'''
    def __init__(self, *args,**kwargs):
        BaseClass.__init__(self,*args[:2],**kwargs)
    klass = type(''.join(random.choice(string.ascii_lowercase) for i in range(10)), 
                (BaseClass,),{"__init__": __init__,
                                "default_keymap":btnkey,
                                "description":btndesc,
                                "image":btnicon,
                                "enable":functools.partial(btncb,activated=True),
                                "disable":functools.partial(btncb,activated=False)
                                })
    return klass

def TriggerBtn(fig,btnname,btnkey,btnicon,btndesc,btncb):
    try:
        btn=fig.canvas.manager.toolmanager.add_tool(btnname, TrigButtonFactory(btnkey,btnicon,btndesc,btncb))
        btn.set_figure(fig)
        fig.canvas.manager.toolbar.add_tool(btn,"default_group")
        return btn
    except:
        import wx
        id=wx.NewIdRef()
        btn=fig.canvas.GetParent().toolbar.AddTool( id, 
                                            btnname, 
                                            wx.Bitmap(btnicon), 
                                            shortHelp=btndesc,
                                            kind=wx.ITEM_NORMAL)
        fig.canvas.GetParent().Bind(wx.EVT_TOOL, btncb, id=id)
        fig.canvas.GetParent().toolbar.Realize()
        return btn

def ToggleBtn(fig,btnname,btnkey,btnicon,btndesc,btncb):
    try:
        btn=fig.canvas.manager.toolmanager.add_tool(btnname, ToggleButtonFactory(btnkey,btnicon,btndesc,btncb))
        btn.set_figure(fig)
        fig.canvas.manager.toolbar.add_tool(btn,"default_group")
        return btn
    except:
        import wx
        id=wx.NewIdRef()
        btn=fig.canvas.GetParent().toolbar.AddTool( id, 
                                            btnname, 
                                            wx.Bitmap(btnicon), 
                                            shortHelp=btndesc,
                                            kind=wx.ITEM_CHECK)
        fig.canvas.GetParent().Bind(wx.EVT_TOOL, btncb, id=id)
        fig.canvas.GetParent().toolbar.Realize()
        return btn

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    def figure_ctb(*args, **kwargs):
        """matplotlib.pyplot.figure with custom toolbar"""
        fig = _plt.figure(*args, **kwargs)
        btn1=TriggerBtn(fig,'prev','p','../resources/exit.png','Switch to prev frame',lambda cls,*args,**kwargs:cls.figure.patch.set_facecolor('red') or cls.figure.canvas.draw())
        btn2=TriggerBtn(fig,'next','n','../resources/redo.png','Switch to next frame',lambda cls,*args,**kwargs:print(cls.__dict__))
        btn3=ToggleBtn(fig,'toggle','t','../resources/fa-trash-solid.png','Toggle some fancy drawing',lambda event,activated:print(event,activated))
        return fig
    fig = figure_ctb()
    # Alternative:
    # fig = plt.figure()
    # pan_zoom = PanAndZoom(fig)

    nrow, ncol = 2, 3

    ax1 = fig.add_subplot(nrow, ncol, 1)
    ax1.set_title('basic')
    ax1.plot((1, 2, 3))

    ax2 = fig.add_subplot(nrow, ncol, 2)
    ax2.set_title('log + twinx')
    ax2.set_yscale('log')
    ax2.plot((1, 2, 1))

    ax2bis = ax2.twinx()
    ax2bis.plot((3, 2, 1), color='red')

    ax3 = fig.add_subplot(nrow, ncol, 3)
    ax3.set_title('inverted y axis')
    ax3.plot((1, 2, 3))
    lim = ax3.get_ylim()
    ax3.set_ylim(lim[1], lim[0])

    ax4 = fig.add_subplot(nrow, ncol, 4)
    ax4.set_title('keep ratio')
    ax4.axis('equal')
    ax4.imshow(numpy.arange(100).reshape(10, 10))

    ax5 = fig.add_subplot(nrow, ncol, 5)
    ax5.set_xlabel('symlog scale + twiny')
    ax5.set_xscale('symlog')
    ax5.plot((1, 2, 3))
    ax5bis = ax5.twiny()
    ax5bis.plot((3, 2, 1), color='red')

    # The following is taken from:
    # http://matplotlib.org/examples/axes_grid/demo_curvelinear_grid.html
    from mpl_toolkits.axisartist import Subplot
    from mpl_toolkits.axisartist.grid_helper_curvelinear import \
        GridHelperCurveLinear

    def tr(x, y):  # source (data) to target (rectilinear plot) coordinates
        x, y = numpy.asarray(x), numpy.asarray(y)
        return x + 0.2 * y, y - x

    def inv_tr(x, y):
        x, y = numpy.asarray(x), numpy.asarray(y)
        return x - 0.2 * y, y + x

    grid_helper = GridHelperCurveLinear((tr, inv_tr))

    ax6 = Subplot(fig, nrow, ncol, 6, grid_helper=grid_helper)
    fig.add_subplot(ax6)
    ax6.set_title('non-ortho axes')

    xx, yy = tr([3, 6], [5.0, 10.])
    ax6.plot(xx, yy)

    ax6.set_aspect(1.)
    ax6.set_xlim(0, 10.)
    ax6.set_ylim(0, 10.)

    ax6.axis["t"] = ax6.new_floating_axis(0, 3.)
    ax6.axis["t2"] = ax6.new_floating_axis(1, 7.)
    ax6.grid(True)

    plt.show()
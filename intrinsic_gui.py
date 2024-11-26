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
import datetime
from pathlib import Path
import wx
from wx import stc
from wx.lib import sheet
import wx.richtext as rt
import pandas as pd

import intrinsic as itsq
from config import cfg

## not required here but forces pyinstaller to include the modules
import matplotlib
import matplotlib.backends.backend_wxagg

#mostly copied from wxPython demos and stackoverflow
if wx.Platform == '__WXMSW__':
    faces = { 'times': 'Times New Roman',
              'mono' : 'Courier New',
              'helv' : 'Arial',
              'other': 'Courier New',
              'size' : 10,
              'size2': 8,
             }
elif wx.Platform == '__WXMAC__':
    faces = { 'times': 'Times New Roman',
              'mono' : 'Monaco',
              'helv' : 'Arial',
              'other': 'Comic Sans MS',
              'size' : 10,
              'size2': 10,
             }
else:
    faces = { 'times': 'Times',
              'mono' : 'Courier',
              'helv' : 'Helvetica',
              'other': 'new century schoolbook',
              'size' : 10,
              'size2': 10,
             }
## https://stackoverflow.com/questions/28509629/work-with-ctrl-c-and-ctrl-v-to-copy-and-paste-into-a-wx-grid-in-wxpython
class CpGrid(wx.grid.Grid):
    """ A Full Copy and Paste enabled grid class which implements Excel
    like copy, paste, and delete functionality.

    Ctrl+c - Copy range of selected cells.
    Ctrl+v - Paste copy selection at point of currently selected cell.
             If paste selection is larger than copy selection,
             copy selection will be replicated to fill paste
             region if it is a modulo number of copy rows and/or
             columns, otherwise just the copy selection will be pasted.
    Ctrl+x - Delete current selection. Deleted selection can be
             restored with Ctrl+z, or pasted with Ctrl+v.
             Delete or backspace key will also perform this action.
    Ctrl+z - Undo the last paste or delete action.

    """

    def __init__(self, parent, id, style):
        wx.grid.Grid.__init__(self, parent, id, wx.DefaultPosition,
                              wx.DefaultSize, style)

        # bind key down events
        wx.EVT_KEY_DOWN(self, self.OnKey)

        # initialize text string for undo (start row, start col, undo string)
        self.data4undo = [0, 0, '']

        # initialize copy rows and columns
        # catches case of initial Ctrl+v before a Ctrl+c
        self.crows = 1
        self.ccols = 1

        # initialize clipboard to empty string
        data = ''

        # Create text data object
        clipboard = wx.TextDataObject()

        # Set data object value
        clipboard.SetText(data)

        # Put the data in the clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(clipboard)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Can't open the clipboard", "Error")

    def OnKey(self, event):
        '''Handles all key events.
        '''

        # If Ctrl+c is pressed...
        if event.ControlDown() and event.GetKeyCode() == 67:
            self.copy()

        # If Ctrl+v is pressed...
        if event.ControlDown() and event.GetKeyCode() == 86:
            self.paste('paste')

        # If Ctrl+Z is pressed...
        if event.ControlDown() and event.GetKeyCode() == 90:
            if self.data4undo[2] != '':
                self.paste('undo')

        # If del, backspace or Ctrl+x is pressed...
        if event.GetKeyCode() == 127 or event.GetKeyCode() == 8 \
                or (event.ControlDown() and event.GetKeyCode() == 88):
            # Call delete method
            self.delete()

        # Skip other Key events
        if event.GetKeyCode():
            event.Skip()
            return

    def copy(self):
        '''Copies the current range of select cells to clipboard.
        '''
        # Get number of copy rows and cols
        if self.GetSelectionBlockTopLeft() == []:
            rowstart = self.GetGridCursorRow()
            colstart = self.GetGridCursorCol()
            rowend = rowstart
            colend = colstart
        else:
            rowstart = self.GetSelectionBlockTopLeft()[0][0]
            colstart = self.GetSelectionBlockTopLeft()[0][1]
            rowend = self.GetSelectionBlockBottomRight()[0][0]
            colend = self.GetSelectionBlockBottomRight()[0][1]

        self.crows = rowend - rowstart + 1
        self.ccols = colend - colstart + 1

        # data variable contains text that must be set in the clipboard
        data = ''

        # For each cell in selected range append the cell value
        # in the data variable Tabs '\t' for cols and '\n' for rows
        for r in range(self.crows):
            for c in range(self.ccols):
                data += str(self.GetCellValue(rowstart + r, colstart + c))
                if c < self.ccols - 1:
                    data += '\t'
            data += '\n'

        # Create text data object
        clipboard = wx.TextDataObject()

        # Set data object value
        clipboard.SetText(data)

        # Put the data in the clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(clipboard)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Can't open the clipboard", "Error")

    def build_paste_selection(self):
        '''This method creates the paste selection, builds it
        into a clipboard string, and puts it on the clipboard.
        When building the paste selection it fills in replicas
        of the copy selection if: number of rows and/or columns
        in the paste selection is larger than the copy selection,
        and they are multiples of the corresponding copy selection
        rows and/or columns, otherwise just the copy selection
        will be used.
        '''

        # Get number of copy rows and cols
        if self.GetSelectionBlockTopLeft() == []:
            rowstart = self.GetGridCursorRow()
            colstart = self.GetGridCursorCol()
            rowend = rowstart
            colend = colstart
        else:
            rowstart = self.GetSelectionBlockTopLeft()[0][0]
            colstart = self.GetSelectionBlockTopLeft()[0][1]
            rowend = self.GetSelectionBlockBottomRight()[0][0]
            colend = self.GetSelectionBlockBottomRight()[0][1]

        self.prows = rowend - rowstart + 1
        self.pcols = colend - colstart + 1

        # find if paste selection area is a multiple of the copy selection
        rows_mod = not(bool(self.prows % self.crows))
        cols_mod = not(bool(self.pcols % self.ccols))

        # initialize to default case (i.e. paste equals copy)
        row_copies = 1
        col_copies = 1

        # one row multiple column paste selection
        if self.prows == 1 and self.pcols > 1 and cols_mod:
            col_copies = self.pcols / self.ccols  # int division

        # one col multiple row paste selection
        if self.prows > 1 and rows_mod and self.pcols == 1:
            row_copies = self.prows / self.crows  # int division

        # mulitple row and column paste selection
        if self.prows > 1 and rows_mod and self.pcols > 1 and cols_mod:
            row_copies = self.prows / self.crows  # int division
            col_copies = self.pcols / self.ccols  # int division

        clipboard = wx.TextDataObject()
        if wx.TheClipboard.Open():
            wx.TheClipboard.GetData(clipboard)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Can't open the clipboard", "Error")

        data = clipboard.GetText()

        # column expansion (fill out additional columns)
        out_values = []
        for row, text in enumerate(data.splitlines()):
            string = text
            for i in range(col_copies - 1):
                string += '\t' + text
            out_values.append(string)

        # row expansion (fill out additional rows)
        out_values *= row_copies

        # build output text string for clipboard
        self.out_data = '\n'.join(out_values)

    def paste(self, mode):
        '''Handles paste and undo operations.
        '''

        # perform paste or undo action
        if mode == 'paste':
            # create the paste string from the copy string
            self.build_paste_selection()

            if self.GetSelectionBlockTopLeft() == []:
                rowstart = self.GetGridCursorRow()
                colstart = self.GetGridCursorCol()
            else:
                rowstart = self.GetSelectionBlockTopLeft()[0][0]
                colstart = self.GetSelectionBlockTopLeft()[0][1]
        elif mode == 'undo':
            self.out_data = self.data4undo[2]
            rowstart = self.data4undo[0]
            colstart = self.data4undo[1]
        else:
            wx.MessageBox("Paste method " + mode + " does not exist", "Error")

        # paste current paste selection and build a clipboard string for undo
        text4undo = ''  # initialize
        for y, r in enumerate(self.out_data.splitlines()):
            # Convert c in a array of text separated by tab
            for x, c in enumerate(r.split('\t')):
                if y + rowstart < self.NumberRows and \
                        x + colstart < self.NumberCols:
                    text4undo += str(self.GetCellValue(rowstart + y,
                                                       colstart + x)) + '\t'
                    self.SetCellValue(rowstart + y, colstart + x, c)

            text4undo = text4undo[:-1] + '\n'

        # save current paste selection for undo
        if mode == 'paste':
            self.data4undo = [rowstart, colstart, text4undo]
        else:
            self.data4undo = [0, 0, '']

    def delete(self):
        '''This method deletes text from selected cells, places a
        copy of the deleted cells on the clipboard for pasting
        (Ctrl+v), and places a copy in the self.data4undo variable
        for undoing (Ctrl+z)
        '''

        # Get number of delete rows and cols
        if self.GetSelectionBlockTopLeft() == []:
            rowstart = self.GetGridCursorRow()
            colstart = self.GetGridCursorCol()
            rowend = rowstart
            colend = colstart
        else:
            rowstart = self.GetSelectionBlockTopLeft()[0][0]
            colstart = self.GetSelectionBlockTopLeft()[0][1]
            rowend = self.GetSelectionBlockBottomRight()[0][0]
            colend = self.GetSelectionBlockBottomRight()[0][1]

        rows = rowend - rowstart + 1
        cols = colend - colstart + 1

        # Save deleted text and clear cells contents
        text4undo = ''
        for r in range(rows):
            for c in range(cols):
                text4undo += \
                    str(self.GetCellValue(rowstart + r, colstart + c)) + '\t'
                self.SetCellValue(rowstart + r, colstart + c, '')

            text4undo = text4undo[:-1] + '\n'

        # Save a copy of deleted text for undo
        self.data4undo = [rowstart, colstart, text4undo]

        # Save a copy of deleted text to clipboard for Ctrl+v
        clipboard = wx.TextDataObject()
        clipboard.SetText(text4undo)
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(clipboard)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Can't open the clipboard", "Error")

class FileDrop(wx.FileDropTarget):
    def __init__(self, window):
        wx.FileDropTarget.__init__(self)
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        self.window.SetValue(filenames[0])
        return True

class PythonSTC(stc.StyledTextCtrl):
    def __init__(self, parent, ID,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=0):
        stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)
        self.SetLexer(stc.STC_LEX_PYTHON)
        self.SetViewWhiteSpace(False)
        self.StyleSetSpec(stc.STC_STYLE_DEFAULT,     "face:%(helv)s,size:%(size)d" % faces)
        self.StyleClearAll()  # Reset all to be like the default

        # Default
        '''
        self.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#000000,face:%(helv)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#007F00,face:%(other)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_NUMBER, "fore:#007F7F,bold,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_STRING, "fore:#7F007F,face:%(helv)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#7F007F,face:%(helv)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_WORD, "fore:#00007F,bold,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#7F0000,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#7F0000,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#0000FF,bold,underline,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#007F7F,bold,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_OPERATOR, "bold,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#000000,face:%(helv)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:#7F0000,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_STRINGEOL, "fore:#000000,face:%(mono)s,back:#E0C0E0,eol,size:%(size)d" % faces)
        '''
        self.StyleSetSpec(stc.STC_P_DEFAULT, "fore:#000000,face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_COMMENTLINE,"fore:#7F0000,face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_NUMBER, "fore:#007F7F,face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_STRING, "fore:#7F007F,face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#7F007F,face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_WORD, "fore:#00007F,face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_TRIPLE, "fore:#7F0000,face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_TRIPLEDOUBLE, "fore:#7F0000,face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#0000FF,face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#007F7F,face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_OPERATOR, "face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_IDENTIFIER, "fore:#000000,face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_COMMENTBLOCK, "fore:#7F0000,face:%(mono)s,size:%(size)d" % faces)
        self.StyleSetSpec(stc.STC_P_STRINGEOL, "fore:#000000,face:%(mono)s,back:#E0C0E0,eol,size:%(size)d" % faces)

#https://stackoverflow.com/questions/2819791/how-can-i-redirect-the-logger-to-a-wxpython-textctrl-using-a-custom-logging-hand
class WxTextCtrlHandler(logging.Handler):
    def __init__(self, ctrl):
        logging.Handler.__init__(self)
        self.ctrl = ctrl
        self.lines=0
        self.colors={'DEBUG':wx.TextAttr(wx.Colour("blue")),\
                     'INFO':wx.TextAttr(wx.Colour("forest green")),\
                     'Level':wx.TextAttr(wx.Colour("maroon")),\
                     'WARNING':wx.TextAttr(wx.Colour("magenta")),\
                     'ERROR':wx.TextAttr(wx.Colour("red")),\
                     'CRITICAL':wx.TextAttr(wx.Colour("orange"))}

    def emit(self, record):
        s = self.format(record) + '\n'
        self.lines+=1
        try:
            self.ctrl.SetDefaultStyle(self.colors[s.split(' ')[0]])
        except:
            pass
        self.ctrl.AppendText(s.replace("Level 25",'INFO'))
        
        self.ctrl.ScrollLines(self.lines+1)
        self.ctrl.ShowPosition(self.ctrl.GetLastPosition())
        wx.Yield()

class Example(wx.Frame):
    def __init__(self, *args, **kw):
        super(Example, self).__init__(*args, **kw)
        self.InitUI()
        self.disable_filter=True

    def OnToolbar(self, event):
        if event.GetId()==2:
            wx.Exit() ## cxfreeze removes the site initialization which normally sets up builtins.exit
        elif event.GetId()==1:
            inpath=Path(self.position.GetValue())
            for name,ctl in self.tabs.items():
                with open(Path(__file__).resolve().parent/"params"/(name+".py"),"w") as f:
                    f.write(ctl.GetValue())
            ## blocking process!! this should be started as a thread!
            self.process(inpath)
        elif event.GetId()==3:
            self.disable_filter=not self.disable_filter
            try:
                self.dump()
            except:
                pass

    def dump(self):
        keys=self.df.index if self.disable_filter else itsq.filterfields()
        self.res_sheet.ClearGrid()
        ## our dataframe is an array of tuples (magnitude,dimension_str), but contains nan!
        for row,key in enumerate(keys):
            self.res_sheet.SetCellValue(row,0,str(key))
            self.res_sheet.SetCellTextColour(row,0, "red")
            for col in range(len(self.df.columns)):
                try:
                    #value may be np.nan, but as we're in a try/except block, we don't need to test
                    value=self.df[col][key] ## can't use iloc here
                    self.res_sheet.SetCellValue(row,col+1,str(value)) ## actual value
                    #self.res_sheet.SetCellValue(row,1,str(value[1])) ## units
                    #self.res_sheet.SetCellTextColour(row,1, "green")
                except:
                    pass
            self.notebook.SetSelection(0)
        self.res_sheet.AutoSizeColumns()

    def process(self,inpath):
        '''process the path given as inpath
        inpath may be single file, folder with files, or folder with folders with files'''
        logging.getLogger('intrinsic').log(logging.INFO+5,f"#########################################")
        logging.getLogger('intrinsic').log(logging.INFO+5,f"Analysis started at {datetime.datetime.now().strftime('%H:%M:%S')} ")
        logging.getLogger('intrinsic').log(logging.INFO+5,f"#########################################")
        self.notebook.SetSelection(1) ## switch to log panel
        logging.getLogger('intrinsic').setLevel(globals()['cfg'].ITSQ_LOG_LEVEL)
        ## start processing
        self.df=itsq.process(str(inpath),self.disable_filter)
        ## update the grid
        '''
        self.res_sheet.ClearGrid()
        for row,idx in enumerate(df.index):
            self.res_sheet.SetCellValue(row,0,str(idx))
            self.res_sheet.SetCellTextColour(row,0, "red")
        for col,serie in enumerate(df):
            for row,value in enumerate(df[serie]):
                self.res_sheet.SetCellValue(row,col+1,str(value))
        
        self.res_sheet.AutoSizeColumns()
        '''
        self.dump()
        logging.getLogger('intrinsic').log(logging.INFO+5,f"#########################################")
        logging.getLogger('intrinsic').log(logging.INFO+5,f"Analysis Ended at {datetime.datetime.now().strftime('%H:%M:%S')} ")
        logging.getLogger('intrinsic').log(logging.INFO+5,f"#########################################")
        self.notebook.SetSelection(0)
      
    def InitUI(self):
        self.logger=logging.getLogger('intrinsinc')
        box = wx.BoxSizer(wx.VERTICAL)
        toolbar = wx.ToolBar(self, wx.TB_HORIZONTAL | wx.TB_TEXT)
        toolbar.SetToolBitmapSize((32,32))
        toolbar.AddTool(1, '', wx.Bitmap('resources/redo.png'))
        toolbar.AddTool(2, '', wx.Bitmap('resources/exit.png'))
        toolbar.AddSeparator()
        toolbar.AddCheckTool(3, '', wx.Bitmap('resources/filter.png'))
        toolbar.ToggleTool(3,True)
        box.Add(toolbar)
        toolbar.Realize()
        self.SetSizer(box)
        toolbar.Bind(wx.EVT_TOOL, self.OnToolbar)
        
        self.position = wx.TextCtrl(self)
        dt = FileDrop(self.position)
        self.position.SetDropTarget(dt)
        box.Add(self.position,0, wx.EXPAND)
        #toolbar.AddControl(self.position)

        self.notebook = wx.Notebook(self, style=wx.RIGHT)
        self.res_sheet = CpGrid(self.notebook, -1, wx.WANTS_CHARS)
        self.res_sheet.CreateGrid(2048, 2048)
        self.notebook.AddPage(self.res_sheet, "Results")
        ## logging tab*
        self.logpanel=wx.TextCtrl(self.notebook, wx.ID_ANY,style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL | wx.TE_RICH)
        self.loghandler = WxTextCtrlHandler(self.logpanel)
        logging.getLogger('intrinsic').addHandler(self.loghandler)
        self.loghandler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        logging.getLogger('intrinsic').setLevel(globals()['cfg'].ITSQ_LOG_LEVEL)
        self.notebook.AddPage(self.logpanel, "Logging")
        ## the other sheets are loaded dynamically from config files
        self.tabs={}
        for f in sorted(Path(__file__).parent.glob("params/*_params*.py")):
            if str(f.name).startswith('_'):
                continue
            param_stc=PythonSTC(self.notebook,2)
            param_stc.SetLexerLanguage("python")      # does not work
            param_stc.SetText(open(f,"r").read())
            param_stc.StyleSetSpec(wx.stc.STC_P_COMMENTLINE, "back:#fdf6e3,fore:#93a1a1,face:Ubuntu Mono,size:11") 
            self.notebook.AddPage(param_stc, f.stem)
            self.tabs[f.stem]=param_stc
   
        self.res_sheet.SetFocus()
        box.Add(self.notebook, 1, wx.EXPAND)
        self.CreateStatusBar()
        self.SetSize((850, 550))
        self.SetTitle("Drag/Drop files or folders Text entry zone")
        self.Centre()

def main():
    redir=False
    app = wx.App(redirect=redir)
    ex = Example(None)
    ex.Show()
    #if not redir:
    #    itsq.patchlogger()
    app.MainLoop()


if __name__ == '__main__':
    from config import cfg
    #itsq.updateparams("./params/generic_params.py")
    main()

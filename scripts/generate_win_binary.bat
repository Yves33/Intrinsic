@echo off
cd ..
del /s /q /f *.pyc
SET TARGET=intrinsic_gui
pyinstaller.exe --clean ^
-p ./modules/ ^
--additional-hooks-dir=hooks ^
--exclude-module FixTk ^
--exclude-module tcl ^
--exclude-module _tkinter ^
--exclude-module tkinter ^
--exclude-module Tkinter ^
--exclude-module tk ^
--exclude-module win32com ^
--exclude-module pywin32 ^
--exclude-module pubsub ^
--exclude-module smokesignal ^
--exclude tornado ^
--exclude jedi ^
--exclude numba ^
--hidden-import wx ^
--hidden-import wx._xml ^
--hidden-import matplotlib.backends.backend_wxagg ^
%TARGET%.py
xcopy /e /Y /i params dist\%TARGET%\params
xcopy /e /Y /i resources dist\%TARGET%\resources
xcopy /e /Y /i scripts\intrinsic.bat dist\
pause
@echo on    
set PATH=%PATH%;%userprofile%\Anaconda3\Scripts
rem %windir%\system32\cmd.exe "/K" %userprofile%\Anaconda3\Scripts\activate.bat ephy & python intrinsic_gui.py
call %userprofile%\Anaconda3\Scripts\activate.bat ephy
python abfutils.py
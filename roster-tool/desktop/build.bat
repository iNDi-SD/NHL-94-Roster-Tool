@echo off
set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
set PI=%LOCALAPPDATA%\Programs\Python\Python312\Scripts\pyinstaller.exe

echo Building NHL '94 Roster Tool for Windows...
"%PI%" --onefile --windowed --name "NHL94 Roster Tool" --icon=icon.ico --add-data "window.ico;." --add-data "cover.png;." roster_tool.py
echo.
echo Done. Find "NHL94 Roster Tool.exe" in the dist\ folder.
echo Drop cover.png next to the .exe to show the box art image.
pause

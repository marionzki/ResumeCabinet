@echo off
cd /d "%~dp0"
pyinstaller --noconfirm ResumeCabinet.spec
if errorlevel 1 exit /b 1
python tools\prepare_distribution_data.py
if errorlevel 1 exit /b 1
echo Build listo: ResumeCabinet.exe y dist\data\

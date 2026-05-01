@echo off
setlocal

echo [1/3] Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [2/3] Cleaning previous one-file build...
if exist build rmdir /s /q build
if exist dist\ResumeCabinet.exe del /q dist\ResumeCabinet.exe

echo [3/3] Building single executable...
python -m PyInstaller --noconfirm --clean --windowed --onefile --name ResumeCabinet ^
 --add-data "images;images" ^
 --add-data "model;model" ^
 --add-data "utils;utils" ^
 --add-data "view_flet;view_flet" ^
 --add-data "controller;controller" ^
 --add-data "references;references" ^
 --collect-data "flet_desktop" ^
 --collect-data "flet" ^
 main_flet.py
if errorlevel 1 goto :error

echo.
echo Build completed successfully.
echo Executable: dist\ResumeCabinet.exe
exit /b 0

:error
echo.
echo Build failed.
exit /b 1

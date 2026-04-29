@echo off
setlocal

echo [1/3] Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo [2/3] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [3/3] Building Windows executable...
python -m PyInstaller --noconfirm main_flet.spec
if errorlevel 1 goto :error

if exist "build\main_flet\main_flet.exe" del /q "build\main_flet\main_flet.exe"

echo.
echo Build completed successfully.
echo Executable: dist\main_flet\main_flet.exe
echo NOTE: Run ONLY the executable inside dist\main_flet
exit /b 0

:error
echo.
echo Build failed.
exit /b 1

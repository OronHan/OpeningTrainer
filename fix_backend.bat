@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo      Chess Opening Trainer - Repair
echo ==========================================
echo.
echo The script needs to know where 'python.exe' is located.
echo If you don't know, you can usually find it in:
echo C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python314\python.exe
echo.

set /p PYTHON_PATH="Enter full path to python.exe (or just press Enter to try 'python'): "
if "!PYTHON_PATH!"=="" set PYTHON_PATH=python

REM Remove quotes if user added them (e.g. via drag-drop)
set PYTHON_PATH=!PYTHON_PATH:"=!

echo.
echo [0/3] Verifying Python path...
"!PYTHON_PATH!" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo CRITICAL ERROR: The command "!PYTHON_PATH!" did not work.
    echo SAFETY CHECK: Aborting. No files were deleted.
    echo Please ensure Python is installed and the path is correct.
    pause
    exit /b
)

echo.
echo [1/3] Cleaning up old environment...
if exist venv rmdir /s /q venv

echo [2/3] Creating new virtual environment...
"!PYTHON_PATH!" -m venv venv

if not exist venv\Scripts\activate (
    echo.
    echo Error: Could not create venv. The path provided might be incorrect.
    pause
    exit /b
)

echo [3/3] Installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt
pip install python-multipart

echo.
echo Done! You can now run 'run.bat'.
pause

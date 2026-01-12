@echo off
echo Starting Chess Opening Trainer...

REM Check if npm is installed
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Node.js is not installed or not in PATH.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b
)
REM Check if venv exists
if not exist venv (
    echo Error: Python virtual environment "venv" not found.
    echo Please run fix_backend.bat first to set it up.
    pause
    exit /b
)

REM Start Backend in a new window
start "Backend API" cmd /k "venv\Scripts\activate && python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

REM Start Frontend in a new window
cd frontend
if exist node_modules\.vite rmdir /s /q node_modules\.vite
echo Installing dependencies...
call npm install
echo Building frontend...
call npm run build
start "Frontend UI" cmd /k "npm run dev -- --port 3000"
cd ..

echo.
echo Backend and Frontend are starting in separate windows.
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:3000
pause
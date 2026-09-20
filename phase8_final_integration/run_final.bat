@echo off
REM =========================================================================
REM  AI Smart Drainage - Final Integration (Phase 8)
REM  YOLO Detection + Tracking + Counting + ESP32 Serial Communication
REM  Easy run script for Windows
REM
REM  What this script does:
REM   1. Creates a virtual environment (venv) if it doesn't already exist.
REM   2. Activates the virtual environment.
REM   3. Installs required packages from requirements.txt.
REM   4. Runs main_final.py (opens webcam + detection + tracking +
REM      counting, and sends ESP32 serial commands if USE_ESP32 = True).
REM =========================================================================

echo ==============================================================
echo  AI Smart Drainage - Final Integration (Phase 8)
echo  Detection + Tracking + Counting + ESP32 Communication
echo ==============================================================

REM Move to the folder where this batch file is located.
cd /d "%~dp0"

REM --- Step 1: Create virtual environment if missing ---
if not exist "venv\" (
    echo [INFO] Creating virtual environment "venv" ...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        echo         Make sure Python is installed and added to PATH.
        pause
        exit /b 1
    )
)

REM --- Step 2: Activate virtual environment ---
echo [INFO] Activating virtual environment ...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

REM --- Step 3: Install requirements ---
echo [INFO] Installing/checking required packages ...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

REM --- Step 4: Run the final integrated program ---
echo [INFO] Starting AI Smart Drainage - Final Integration ...
echo [INFO] Press R to reset counts. Press Q in the video window to quit.
echo [INFO] Check main_final.py / serial_controller.py for USE_ESP32,
echo        CAMERA_INDEX, and SERIAL_PORT settings.
python main_final.py

echo.
echo [INFO] Program finished. Press any key to close this window.
pause >nul

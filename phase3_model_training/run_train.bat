@echo off
REM ===========================================================
REM AI Smart Drainage - Phase 3: YOLO Model Training
REM Windows helper script
REM
REM This script will:
REM   1. Create a virtual environment named "venv" if it does not
REM      already exist.
REM   2. Activate that virtual environment.
REM   3. Install/update the required Python packages.
REM   4. Run train.py to train the YOLO11 model.
REM ===========================================================

setlocal

echo ============================================================
echo AI Smart Drainage - Phase 3: YOLO Model Training
echo ============================================================
echo.

REM --- Step 1: Check Python is installed -----------------------
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python was not found on this computer.
    echo Please install Python 3.9 or newer from https://www.python.org/downloads/
    echo and make sure "Add Python to PATH" is checked during installation.
    pause
    exit /b 1
)

REM --- Step 2: Create virtual environment if missing ------------
if not exist "venv\" (
    echo Creating virtual environment "venv"...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment "venv" already exists. Skipping creation.
)

REM --- Step 3: Activate virtual environment ----------------------
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate the virtual environment.
    pause
    exit /b 1
)

REM --- Step 4: Install requirements --------------------------------
echo.
echo Installing/updating required packages from requirements.txt ...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install required packages.
    echo Check your internet connection and try again.
    pause
    exit /b 1
)

REM --- Step 5: Run training -----------------------------------------
echo.
echo Starting training...
echo.
python train.py

echo.
echo ============================================================
echo Script finished. Check the messages above for the location
echo of best.pt, or any error explanations if training failed.
echo ============================================================
pause

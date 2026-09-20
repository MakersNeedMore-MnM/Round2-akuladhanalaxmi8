@echo off
echo ========================================
echo Phase 6 - ESP32 Serial Communication
echo ========================================
echo.
echo Installing/checking requirements...
pip install -r requirements.txt

echo.
echo Starting Python Sender (Test Mode)...
echo.
python python_sender.py

pause

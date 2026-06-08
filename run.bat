@echo off
REM Quick start script for Windows

echo ========================================
echo Sensor Data Annotation Tool
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo Python found!
echo.

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Dependencies not installed. Installing now...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo Dependencies OK!
echo.

REM Generate sample data if not exists
if not exist "sample_data\sample_sensor_data.csv" (
    echo Generating sample data...
    python generate_sample_data.py
    echo.
)

REM Run the application
echo Starting Sensor Data Annotation Tool...
echo.
python src\main.py

pause

@echo off
echo =========================================
echo    Traffic Management System
echo =========================================

set SUMO_HOME=C:\Program Files (x86)\Eclipse\Sumo
set PATH=%SUMO_HOME%\bin;%PATH%
set PYTHONPATH=%cd%

cd /d %~dp0

if not exist simulator\core.py (
    echo Simulator module not found!
    pause
    exit /b
)

echo Starting simulation...
python -c "from simulator.core import run_simulation; run_simulation(duration=100)"

echo.
echo Simulation finished!
pause
@echo off
REM Double-click this file, or run it from the project folder.
cd /d "%~dp0"
py -3 run_demo.py
if errorlevel 1 python run_demo.py

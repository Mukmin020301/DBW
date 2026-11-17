@echo off
title DBW Serial Oscilloscope
echo ========================================================
echo Starting Focus Applied Tech - DBW Serial Scope
echo Target: COM4 @ 115200 Baud
echo ========================================================
python serial_scope.py COM4
pause

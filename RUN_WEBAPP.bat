@echo off
echo Starting DBW Web App...
cd d:\Users\ANG\Desktop\Mukmin\DBW\WebApp

:: Buka browser Edge secara paksa supaya tak keluar error Windows
start msedge http://127.0.0.1:5000

:: Run server python
python app.py

pause

@echo off
echo Stopping AI Rota System...

REM Find and kill the uvicorn process
taskkill /f /im python.exe
taskkill /f /im uvicorn.exe

echo AI Rota System stopped. 
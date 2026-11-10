@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Die Projektumgebung fehlt. Bitte zuerst den Schnellstart in der README ausfuehren.
    exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run app.py

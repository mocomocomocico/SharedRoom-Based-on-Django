@echo off
setlocal
cd /d "%~dp0"

echo [1/3] Creating Python virtual environment...
py -m venv .venv
if errorlevel 1 (
  echo Failed to create virtual environment. Please check that Python is installed and available as py.
  pause
  exit /b 1
)

echo [2/3] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [3/3] Installing backend dependencies from public PyPI...
python -m pip install --upgrade pip -i https://pypi.org/simple
python -m pip install -r requirements.txt -i https://pypi.org/simple
if errorlevel 1 (
  echo Dependency installation failed. Check your network or proxy settings.
  pause
  exit /b 1
)

echo.
echo Backend dependencies installed successfully.
echo Next run: start_backend_windows.bat
pause

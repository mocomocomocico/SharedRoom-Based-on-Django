@echo off
setlocal
cd /d "%~dp0"

if not exist .venv\Scripts\activate.bat (
  echo Python virtual environment not found. Running setup first...
  call setup_backend_windows.bat
)

call .venv\Scripts\activate.bat

REM Default MySQL settings. Change these if your local MySQL user/password/database differ.
set MYSQL_HOST=127.0.0.1
set MYSQL_PORT=3306
set MYSQL_DATABASE=shared_study_room
set MYSQL_USER=root
set MYSQL_PASSWORD=123456

echo Running database migrations...
python manage.py migrate
if errorlevel 1 (
  echo.
  echo Migration failed. Please make sure MySQL is running and the database shared_study_room exists.
  echo SQL: CREATE DATABASE shared_study_room DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  pause
  exit /b 1
)

echo Loading/resetting demo data...
python manage.py reset_demo_data

echo Starting Django backend at http://127.0.0.1:8000/
python manage.py runserver 127.0.0.1:8000
pause

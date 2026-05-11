@echo off
:: Change to the root directory
cd %~dp0..

echo ===================================================
echo Starting Autonomous Fleet Intelligence Platform
echo ===================================================

:: Start Kafka in background
echo [1/5] Starting Kafka (KRaft Mode)...
start "Kafka Broker" cmd /k "cd infrastructure\kafka && bin\windows\kafka-server-start.bat config\kraft\server.properties"

:: Wait for Kafka to boot
echo Waiting 10 seconds for Kafka to initialize...
ping 127.0.0.1 -n 11 > nul

:: Activate Venv
call venv\Scripts\activate.bat

:: Start Backend API
echo [2/5] Starting FastAPI Backend...
start "FastAPI Backend" cmd /k "call venv\Scripts\activate.bat && uvicorn backend.main:app --reload --port 8000"

:: Start Telemetry Consumer
echo [3/5] Starting Telemetry Consumer...
start "Kafka Consumer" cmd /k "call venv\Scripts\activate.bat && python streaming\consumer.py"

:: Start Telemetry Producer
echo [4/5] Starting Telemetry Producer Simulation...
start "Telemetry Simulation" cmd /k "call venv\Scripts\activate.bat && python streaming\producer.py"

:: Start Frontend (Assuming Vite is installed)
echo [5/5] Starting React Frontend...
if exist "frontend\node_modules" (
    start "React Frontend" cmd /k "cd frontend && npm run dev"
) else (
    echo Frontend node_modules not found. Skipping frontend start. Please run 'npm install' in the frontend directory.
)

echo.
echo ===================================================
echo All services started! 
echo Check the individual console windows for logs.
echo Frontend: http://localhost:5173
echo Backend API: http://localhost:8000/docs
echo ===================================================
pause

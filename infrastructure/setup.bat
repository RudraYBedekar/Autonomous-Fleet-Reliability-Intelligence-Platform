@echo off
:: Change to the root directory
cd %~dp0..

echo ===================================================
echo Setting up Autonomous Fleet Intelligence Platform
echo ===================================================

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

:: Activate virtual environment and install dependencies
echo Installing Python dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

:: Download and extract Kafka if it doesn't exist
if not exist "infrastructure\kafka" (
    echo Downloading Apache Kafka...
    mkdir infrastructure\kafka
    cd infrastructure
    curl -O https://downloads.apache.org/kafka/3.7.0/kafka_2.13-3.7.0.tgz
    tar -xzf kafka_2.13-3.7.0.tgz
    xcopy /E /I /Y kafka_2.13-3.7.0\* kafka\
    rmdir /S /Q kafka_2.13-3.7.0
    del kafka_2.13-3.7.0.tgz
    
    echo Formatting Kafka Storage...
    cd kafka
    bin\windows\kafka-storage.bat format -t h73x-v0wTRWg-Z0sQ3H8uw -c config\kraft\server.properties
    cd ..\..
) else (
    echo Kafka is already downloaded and configured.
)

:: Install Frontend Dependencies
if exist "frontend" (
    echo Installing Frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

echo.
echo ===================================================
echo Setup Complete! 
echo You can now run infrastructure\start.bat
echo ===================================================
pause

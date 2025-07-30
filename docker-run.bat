@echo off
echo 🚀 Starting AI Rota System for Healthcare...

REM Check if .env file exists
if not exist .env (
    echo ❌ Error: .env file not found!
    echo Please create a .env file based on env.template with your API keys:
    echo copy env.template .env
    echo Then edit .env and add your API keys:
    echo - OPENAI_API_KEY=your_openai_api_key_here
    echo - GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here (optional)
    pause
    exit /b 1
)

REM Build and start the services
echo 📦 Building and starting services...
docker compose up --build -d

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak > nul

REM Check if services are running
docker compose ps | findstr "Up" > nul
if %errorlevel% equ 0 (
    echo ✅ Services are running!
    echo.
    echo 🌐 Frontend: http://localhost:3000
    echo 🔧 Backend API: http://localhost:8000
    echo 📚 API Documentation: http://localhost:8000/docs
    echo.
    echo To stop the services, run: docker compose down
    echo To view logs, run: docker compose logs -f
) else (
    echo ❌ Error: Services failed to start
    echo Check logs with: docker compose logs
    pause
    exit /b 1
)

pause 
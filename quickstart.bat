@echo off
echo.
echo ========================================
echo FDA Regulatory Automation Platform
echo Quickstart Script
echo ========================================
echo.

REM Check if Docker is running
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo [IMPORTANT] Please edit .env and add your ANTHROPIC_API_KEY
    echo Open .env in a text editor and set:
    echo ANTHROPIC_API_KEY=your-key-here
    echo.
    pause
)

echo.
echo Building Docker containers...
docker-compose build

echo.
echo Starting services...
docker-compose up -d

echo.
echo Waiting for services to start...
timeout /t 15 /nobreak >nul

echo.
echo Checking service health...

REM Check PostgreSQL
docker-compose exec -T postgres pg_isready -U fda_user >nul 2>&1
if errorlevel 1 (
    echo [WARNING] PostgreSQL may not be ready yet
) else (
    echo [OK] PostgreSQL is healthy
)

REM Check Redis
docker-compose exec -T redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Redis may not be ready yet
) else (
    echo [OK] Redis is healthy
)

echo.
echo Seeding database with sample data...
docker-compose exec -T backend python seed_data.py

echo.
echo ========================================
echo Platform is ready!
echo ========================================
echo.
echo Access points:
echo   Frontend:  http://localhost:3400
echo   Backend:   http://localhost:8400
echo   API Docs:  http://localhost:8400/api/docs
echo.
echo Quick actions:
echo   1. Create submission: http://localhost:3400/submit
echo   2. View dashboard:    http://localhost:3400
echo   3. Review queue:      http://localhost:3400/review
echo.
echo Management:
echo   View logs:    docker-compose logs -f
echo   Stop:         docker-compose down
echo   Restart:      docker-compose restart
echo.
pause

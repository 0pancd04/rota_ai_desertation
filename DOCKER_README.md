# Docker Setup for AI Rota System for Healthcare

This guide explains how to run the AI Rota System using Docker and Docker Compose.

## Prerequisites

1. **Docker**: Install Docker Desktop or Docker Engine
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac)
   - [Docker Engine](https://docs.docker.com/engine/install/) (Linux)

2. **Docker Compose**: Usually included with Docker Desktop, or install separately

## Quick Start

### 1. Set up Environment Variables

Create a `.env` file in the project root:

```bash
cp env.template .env
```

Edit `.env` and add your API keys:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Google Maps API Configuration (optional - for accurate travel time calculations)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Application Configuration
DEBUG=True
LOG_LEVEL=INFO
```

### 2. Run the Application

#### Option A: Using the provided scripts

**Linux/Mac:**
```bash
./docker-run.sh
```

**Windows:**
```cmd
docker-run.bat
```

#### Option B: Manual Docker Compose

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Access the Application

Once running, you can access:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Services

The Docker Compose setup includes:

### Backend Service
- **Port**: 8000
- **Technology**: FastAPI (Python)
- **Features**: 
  - AI-powered employee assignment
  - Data processing
  - API endpoints
  - SQLite database

### Frontend Service
- **Port**: 3000
- **Technology**: React + Vite
- **Features**:
  - Modern UI with Tailwind CSS
  - File upload interface
  - Assignment management
  - Real-time data display

## Docker Files

- `Dockerfile.backend`: Python backend container
- `frontend/Dockerfile`: React frontend container
- `docker-compose.yml`: Orchestrates both services
- `.dockerignore`: Excludes unnecessary files from build context

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for AI processing |
| `GOOGLE_MAPS_API_KEY` | No | Google Maps API key for travel time calculations |
| `DEBUG` | No | Enable debug mode (default: True) |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

## Data Persistence

- **Database**: SQLite database is stored in a Docker volume
- **Uploaded Files**: Stored in `./input_files` directory (mounted as volume)
- **Environment**: Loaded from `.env` file

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using the ports
   lsof -i :3000
   lsof -i :8000
   
   # Stop conflicting services or change ports in docker-compose.yml
   ```

2. **API key errors**
   - Ensure your `.env` file exists and contains valid API keys
   - Check the logs: `docker-compose logs backend`

3. **Build failures**
   ```bash
   # Clean and rebuild
   docker-compose down
   docker system prune -f
   docker-compose up --build
   ```

4. **Frontend can't connect to backend**
   - Ensure both services are running: `docker-compose ps`
   - Check backend logs: `docker-compose logs backend`
   - Verify API URL in frontend environment

### Useful Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart a specific service
docker-compose restart backend

# Access container shell
docker-compose exec backend bash
docker-compose exec frontend sh

# Clean up everything
docker-compose down -v
docker system prune -a
```

## Development

For development, you can:

1. **Run services individually**:
   ```bash
   # Backend only
   docker-compose up backend
   
   # Frontend only
   docker-compose up frontend
   ```

2. **Mount source code for live reload**:
   ```bash
   # Add volumes to docker-compose.yml for development
   volumes:
     - ./app:/app/app
     - ./frontend/src:/app/src
   ```

3. **Use development mode**:
   ```bash
   # Frontend development server
   cd frontend && npm run dev
   
   # Backend development server
   cd app && uvicorn main:app --reload
   ```

## Production Deployment

For production:

1. **Use production environment variables**
2. **Set up proper logging**
3. **Configure reverse proxy (nginx)**
4. **Use external database (PostgreSQL/MySQL)**
5. **Set up monitoring and health checks**

## Security Notes

- Never commit `.env` files to version control
- Use strong, unique API keys
- Regularly update dependencies
- Monitor Docker container logs for security issues
- Consider using Docker secrets for sensitive data in production 
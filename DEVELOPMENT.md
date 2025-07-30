# Development Environment Setup

## Overview

This document describes how to set up and use the development environment with hot reloading for the AI Rota System. The development environment allows you to make code changes and see them immediately without rebuilding containers.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- `.env` file configured (copy from `env.template`)

### Start Development Environment
```bash
./dev-start.sh
```

### Stop Development Environment
```bash
./dev-stop.sh
```

### View Logs
```bash
./dev-logs.sh
```

## 🔧 Development Features

### Hot Reloading
- **Backend**: Uses `uvicorn --reload` for automatic Python code reloading
- **Frontend**: Uses Vite dev server for automatic React code reloading
- **Database**: Persistent SQLite database survives restarts
- **Volume Mounts**: Code changes are immediately reflected

### Volume Mounts

#### Backend (`backend-dev`)
```yaml
volumes:
  - ./app:/app/app                    # Python code
  - ./input_files:/app/input_files    # Upload files
  - ./data:/app/data                  # SQLite database
  - ./requirements.txt:/app/requirements.txt
```

#### Frontend (`frontend-dev`)
```yaml
volumes:
  - ./frontend/src:/app/src           # React components
  - ./frontend/public:/app/public     # Static files
  - ./frontend/package.json:/app/package.json
  - ./frontend/vite.config.js:/app/vite.config.js
  - ./frontend/tailwind.config.js:/app/tailwind.config.js
  - ./frontend/postcss.config.js:/app/postcss.config.js
  - ./frontend/index.html:/app/index.html
```

## 📁 File Structure

```
rota_ai_desertation/
├── app/                          # Backend Python code
│   ├── main.py                   # FastAPI application
│   ├── database.py               # Database operations
│   ├── models/                   # Pydantic models
│   └── services/                 # Business logic
├── frontend/                     # Frontend React code
│   ├── src/                      # React components
│   ├── public/                   # Static assets
│   └── package.json              # Dependencies
├── data/                         # SQLite database (persistent)
├── input_files/                  # Upload directory
├── docker-compose.dev.yml        # Development compose
├── dev-start.sh                  # Development startup
├── dev-stop.sh                   # Development stop
└── dev-logs.sh                   # Development logs
```

## 🔄 Development Workflow

### 1. Start Development Environment
```bash
./dev-start.sh
```

### 2. Make Code Changes
- Edit files in `app/` for backend changes
- Edit files in `frontend/src/` for frontend changes
- Changes are automatically detected and reloaded

### 3. View Changes
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. Monitor Logs
```bash
./dev-logs.sh
```

### 5. Stop Development
```bash
./dev-stop.sh
```

## 🛠️ Development Commands

### Manual Docker Commands
```bash
# Start development environment
docker compose -f docker-compose.dev.yml up --build -d

# Stop development environment
docker compose -f docker-compose.dev.yml down

# View logs
docker compose -f docker-compose.dev.yml logs -f

# Restart services
docker compose -f docker-compose.dev.yml restart

# Rebuild containers
docker compose -f docker-compose.dev.yml up --build -d
```

### Backend Development
```bash
# View backend logs only
docker compose -f docker-compose.dev.yml logs -f backend-dev

# Restart backend only
docker compose -f docker-compose.dev.yml restart backend-dev

# Access backend container
docker compose -f docker-compose.dev.yml exec backend-dev bash
```

### Frontend Development
```bash
# View frontend logs only
docker compose -f docker-compose.dev.yml logs -f frontend-dev

# Restart frontend only
docker compose -f docker-compose.dev.yml restart frontend-dev

# Access frontend container
docker compose -f docker-compose.dev.yml exec frontend-dev sh
```

## 🔍 Debugging

### Backend Debugging
1. **Check logs**: `./dev-logs.sh` or `docker compose -f docker-compose.dev.yml logs backend-dev`
2. **API testing**: Use http://localhost:8000/docs for interactive API testing
3. **Database inspection**: SQLite file is at `./data/rota_operations.db`

### Frontend Debugging
1. **Browser DevTools**: Open browser developer tools
2. **Vite DevTools**: Available at http://localhost:3000
3. **Hot reload**: Changes in `frontend/src/` auto-reload

### Database Debugging
```bash
# Check database status
curl http://localhost:8000/data-status

# View database contents
curl http://localhost:8000/database/employees
curl http://localhost:8000/database/patients
curl http://localhost:8000/database/assignments
```

## 📊 Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| **Hot Reload** | ✅ Enabled | ❌ Disabled |
| **Volume Mounts** | ✅ Code mounted | ❌ Code copied |
| **Debug Mode** | ✅ Enabled | ❌ Disabled |
| **Database** | ✅ Persistent | ✅ Persistent |
| **Logging** | ✅ Verbose | ✅ Production level |

## 🚨 Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
lsof -i :8000
lsof -i :3000

# Kill the process or change ports in docker-compose.dev.yml
```

#### 2. Container Won't Start
```bash
# Check logs
docker compose -f docker-compose.dev.yml logs

# Rebuild containers
docker compose -f docker-compose.dev.yml up --build -d
```

#### 3. Hot Reload Not Working
```bash
# Restart the specific service
docker compose -f docker-compose.dev.yml restart backend-dev
docker compose -f docker-compose.dev.yml restart frontend-dev
```

#### 4. Database Issues
```bash
# Check database file
ls -la data/

# Clear database (if needed)
curl -X POST http://localhost:8000/database/clear
```

### Performance Tips

1. **Use `.dockerignore`**: Exclude unnecessary files from Docker context
2. **Limit volume mounts**: Only mount necessary directories
3. **Use development dependencies**: Install only what's needed for development
4. **Monitor resource usage**: Use `docker stats` to monitor container resources

## 🔧 Configuration

### Environment Variables
Create a `.env` file from `env.template`:
```bash
cp env.template .env
```

Required variables:
```env
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
DEBUG=True
LOG_LEVEL=INFO
```

### Custom Ports
Edit `docker-compose.dev.yml` to change ports:
```yaml
ports:
  - "8001:8000"  # Backend on port 8001
  - "3001:3000"  # Frontend on port 3001
```

## 📝 Best Practices

### Code Changes
1. **Backend**: Changes in `app/` auto-reload
2. **Frontend**: Changes in `frontend/src/` auto-reload
3. **Database**: Changes persist across restarts
4. **Configuration**: Restart containers for config changes

### Testing
1. **API Testing**: Use http://localhost:8000/docs
2. **Frontend Testing**: Use browser developer tools
3. **Database Testing**: Use the database endpoints
4. **Integration Testing**: Test full workflow end-to-end

### Deployment
1. **Development**: Use `docker-compose.dev.yml`
2. **Production**: Use `docker-compose.yml`
3. **Database**: Backup `./data/rota_operations.db`
4. **Environment**: Use proper `.env` files

## 🎯 Success Metrics

### Development Environment
- ✅ **Hot Reload**: Backend and frontend changes auto-reload
- ✅ **Database Persistence**: Data survives restarts
- ✅ **Volume Mounts**: Code changes immediately reflected
- ✅ **Easy Commands**: Simple start/stop/logs scripts
- ✅ **Debugging**: Full access to logs and containers

### Performance
- ✅ **Fast Startup**: Development containers start quickly
- ✅ **Efficient Reloads**: Only changed files trigger reloads
- ✅ **Resource Usage**: Minimal resource consumption
- ✅ **Stable**: Reliable development environment

---

**Status**: ✅ **FULLY IMPLEMENTED**

The development environment is now ready with hot reloading for both backend and frontend! 
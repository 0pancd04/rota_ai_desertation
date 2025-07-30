# Healthcare Rota System - Frontend

This is the React frontend for the AI-powered Healthcare Rota System.

## Features

- **Dashboard**: Overview of employees, patients, and assignments
- **Data Upload**: Upload Excel files with employee and patient data
- **Employee Management**: View and search employees with filters
- **Patient Management**: View and search patients with their requirements
- **Assignment Management**: View current assignments and generate weekly rota
- **AI-Powered Assignment**: Create assignments using natural language

## Technology Stack

- **React** with Vite for fast development
- **Tailwind CSS** for styling
- **Zustand** for state management
- **Axios** for API calls
- **Heroicons** for icons

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Make sure the backend is running on `http://localhost:8000`

## Project Structure

```
src/
├── pages/           # Page components
├── store/           # Zustand store
├── App.jsx          # Main app component
├── main.jsx         # Entry point
└── index.css        # Tailwind CSS imports
```

## Usage

1. **Upload Data**: Start by uploading an Excel file with employee and patient data
2. **View Data**: Browse employees and patients in their respective sections
3. **Create Assignments**: Use natural language to create individual assignments
4. **Generate Rota**: Generate a complete weekly rota for all patients

## API Integration

The frontend connects to the backend API at `http://localhost:8000`. All API calls are managed through the Zustand store in `src/store/useStore.js`.

# Mental Health Counseling App with Long-term Memory

A web application for mental health counseling using OpenAI API with advanced long-term memory capabilities.

## Features

- **AI-Powered Counseling**: Uses OpenAI's GPT models for empathetic counseling responses
- **Advanced Memory System**: Naturally extracts and remembers user information including:
  - Name, age, location, occupation
  - Family details and relationships
  - Hobbies and interests
  - Personal concerns and goals
  - Personality traits and important experiences
- **Persistent Memory**: Information is retained across sessions
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS

## Architecture

- **Backend**: FastAPI with in-memory storage
- **Frontend**: React with TypeScript, Vite, and Tailwind CSS
- **AI Integration**: OpenAI API for both counseling responses and information extraction

## Setup

### Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Create environment file:
   ```bash
   cp .env.example .env
   ```

4. Add your OpenAI API key to `.env`:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

5. Start the development server:
   ```bash
   poetry run fastapi dev app/main.py
   ```

### Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create environment file:
   ```bash
   cp .env.example .env
   ```

4. Update the backend URL in `.env` if needed:
   ```
   VITE_API_URL=http://localhost:8000
   ```

5. Start the development server:
   ```bash
   npm run dev
   ```

## Deployment

The application can be deployed using:
- Backend: Fly.io (FastAPI deployment)
- Frontend: Static hosting (Vite build output)

## Memory System

The application uses AI-powered extraction to naturally learn about users from conversations. Unlike simple pattern matching, it uses GPT-4 to analyze messages and extract structured information, making the memory system feel natural and comprehensive.

## Development

This project was developed as a prototype for demonstrating advanced AI memory capabilities in counseling applications.

---

**Link to Devin run**: https://app.devin.ai/sessions/8220e4815342444ab6c0806957afdaa5
**Developed by**: @inai17ibar

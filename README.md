# MathOps Microservice

A lightweight, production-ready microservice that supports three math operations: power, Fibonacci, and factorial.

## Features
- FastAPI async API
- Async worker queue
- SQLite logging
- Pydantic for serialization
- Docker-ready
- Job tracking support via `/result/{job_id}`
- 🆕 Simple built-in web UI available at `/ui`

## Run It
```bash
docker build -t mathops .
docker run -p 8000:8000 -v "%cd%\db:/app/db" mathops
```

## API Example
```bash
POST /calculate
{
  "op": "pow",
  "a": 2,
  "b": 10
}

GET /result/{job_id}
```

## Web UI
Visit [http://localhost:8000/ui](http://localhost:8000/ui) to use the form-based interface.
# MathOps Microservice

A lightweight, production-ready microservice that supports three math operations: power, Fibonacci, and factorial.

## Features
- FastAPI async API
- Async worker queue
- SQLite logging
- Pydantic for serialization
- Docker-ready

## Run It
```bash
docker build -t mathops .
docker run -p 8000:8000 -v "%cd%\db:/app/db" mathops
then open http://localhost:8000/docs in your browser
and use the api
```

## API Example
```bash
POST /calculate
{
  "op": "pow",
  "a": 2,
  "b": 10
}

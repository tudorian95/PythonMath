# MathOps Microservice

A lightweight python microservice that supports three math operations: power, fibonacci, and factorial.

## Tech stack
- Python 3.11 lite
  - FastAPI async API
  - Async worker queue
  - SQLite logging
  - Pydantic for serialization
- Docker-ready

## Build and run
Prerequisites: 
- docker up and running
- git installed

Select an empty folder in which you want to download the repository, 'cd' to folder path
and then run these commands:

```cmd
git clone https://github.com/tudorian95/PythonMath.git

cd .\PythonMath

docker build -t mathops .

for cmd use:
docker run -p 8000:8000 -v "%cd%\db:/app/db" mathops

for powershell use:
docker run -p 8000:8000 -v "C:\Users\tudor\source\repos\PythonMath\db:/app/db" mathops
```

## Interact with the web UI
Visit (http://localhost:8000/ui) to use the form-based interface.
Visit (http://localhost:8000/db) to check the logs of the operations.

## API Example
Visit (http://localhost:8000/docs) to inspect all endpoints.
```
POST /calculate
{
  "op": "pow",
  "a": 2,
  "b": 10
}

GET /result/{job_id}
```

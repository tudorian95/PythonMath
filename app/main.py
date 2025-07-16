import uvicorn
from fastapi import FastAPI
from api import router
from models import Base
from db import engine
from workers import worker
import asyncio

app = FastAPI(title="MathOps Microservice")
app.include_router(router)

Base.metadata.create_all(bind=engine)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(worker())

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

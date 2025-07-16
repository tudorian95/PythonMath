from fastapi import APIRouter
from app.schemas import MathRequest, MathResponse
from app.workers import queue

router = APIRouter()

@router.post("/calculate", response_model=MathResponse)
async def calculate(req: MathRequest):
    await queue.put(req.dict())
    return {"result": -1}
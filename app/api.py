import uuid
from fastapi import APIRouter, HTTPException
from schemas import MathRequest, MathResponse, MathResult
from workers import queue
from db import SessionLocal
from models import MathOperation

router = APIRouter()

@router.post("/calculate", response_model=MathResponse)
async def calculate(req: MathRequest):
    job_id = str(uuid.uuid4())
    session = SessionLocal()
    try:
        db_entry = MathOperation(id=job_id, op=req.op, a=req.a, b=req.b)
        session.add(db_entry)
        session.commit()
    finally:
        session.close()

    await queue.put({"op": req.op, "a": req.a, "b": req.b, "job_id": job_id})
    return {"job_id": job_id}

@router.get("/result/{job_id}", response_model=MathResult)
async def get_result(job_id: str):
    session = SessionLocal()
    try:
        op = session.query(MathOperation).filter_by(id=job_id).first()
        if not op:
            raise HTTPException(status_code=404, detail="Job ID not found")
        return {"result": op.result, "status": op.status}
    finally:
        session.close()

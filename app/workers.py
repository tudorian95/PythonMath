import asyncio
import uuid
from models import MathOperation
from services import calc_pow, calc_fib, calc_fact
from db import SessionLocal

queue = asyncio.Queue()

async def worker():
    while True:
        job = await queue.get()
        session = SessionLocal()
        try:
            op, a, b, job_id = job["op"], job["a"], job.get("b"), job["job_id"]
            result = None
            if op == "pow":
                result = calc_pow(a, b)
            elif op == "fib":
                result = calc_fib(a)
            elif op == "fact":
                result = calc_fact(a)

            db_op = session.query(MathOperation).filter_by(id=job_id).first()
            db_op.result = result
            db_op.status = "done"
            session.commit()
        finally:
            session.close()
            queue.task_done()


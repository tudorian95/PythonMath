import asyncio
from app.services import calc_pow, calc_fib, calc_fact
from app.db import SessionLocal
from app.models import MathOperation

queue = asyncio.Queue()

async def worker():
    while True:
        item = await queue.get()
        session = SessionLocal()
        try:
            op, a, b = item["op"], item["a"], item.get("b")
            if op == "pow":
                result = calc_pow(a, b)
            elif op == "fib":
                result = calc_fib(a)
            elif op == "fact":
                result = calc_fact(a)
            else:
                result = None

            db_entry = MathOperation(op=op, a=a, b=b, result=result)
            session.add(db_entry)
            session.commit()
        finally:
            session.close()
            queue.task_done()

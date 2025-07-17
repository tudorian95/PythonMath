import asyncio
import logging
from models import MathOperation
from services import calc_pow, calc_fib, calc_fact
from db import SessionLocal

queue = asyncio.Queue()
logger = logging.getLogger(__name__)


def perform_operation(op, a, b=None):
    if op == "pow":
        return calc_pow(a, b)
    elif op == "fib":
        return calc_fib(a)
    elif op == "fact":
        return calc_fact(a)
    else:
        raise ValueError("Invalid operation")


async def worker():
    while True:
        task = await queue.get()
        logger.info(f"Processing task with job_id: {task['job_id']}")
        session = SessionLocal()
        try:
            result = perform_operation(task["op"], task["a"], task.get("b"))
            db_entry = session.query(MathOperation).filter_by(
                id=task["job_id"]).first()
            if db_entry:
                db_entry.result = str(result)  # Store result as string
                db_entry.status = "done"
                session.commit()
                logger.info(
                    f"Task completed with job_id: {task['job_id']}, result: {result}")
        except OverflowError:
            logger.error(f"OverflowError for job_id {task['job_id']}")
            db_entry = session.query(MathOperation).filter_by(
                id=task["job_id"]).first()
            if db_entry:
                db_entry.result = "Result too large to process."
                db_entry.status = "failed"
                session.commit()
        except Exception as e:
            logger.error(
                f"Unexpected error for job_id {task['job_id']}: {str(e)}")
            db_entry = session.query(MathOperation).filter_by(
                id=task["job_id"]).first()
            if db_entry:
                db_entry.result = f"Unexpected error: {str(e)}"
                db_entry.status = "failed"
                session.commit()
        finally:
            session.close()
            queue.task_done()

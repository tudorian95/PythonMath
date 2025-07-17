from pydantic import BaseModel, Field
from enum import Enum


class Operation(str, Enum):
    pow = "pow"
    fib = "fib"
    fact = "fact"


class MathRequest(BaseModel):
    op: Operation
    a: int
    b: int | None = None


class MathResponse(BaseModel):
    job_id: str


class MathResult(BaseModel):
    result: str | None = None  # Change result type to str
    status: str

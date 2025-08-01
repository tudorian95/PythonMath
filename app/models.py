from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class MathOperation(Base):
    __tablename__ = "operations"
    id = Column(String, primary_key=True, index=True)
    op = Column(String)
    a = Column(Integer)
    b = Column(Integer, nullable=True)
    result = Column(Integer, nullable=True)
    status = Column(String, default="pending")
    timestamp = Column(DateTime, default=datetime.utcnow)

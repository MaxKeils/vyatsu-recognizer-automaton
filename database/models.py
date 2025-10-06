"""Database models for automaton application."""
from sqlalchemy import Column, BigInteger, String, Integer, JSON, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
import enum
from database.database import Base


class HintLevelEnum(str, enum.Enum):
    NO_HINTS = "NO_HINTS"
    LIGHT_HINTS = "LIGHT_HINTS" 
    FULL_HINTS = "FULL_HINTS"


class Configuration(Base):
    __tablename__ = "configuration"
    
    id = Column(Integer, primary_key=True, default=1)
    duration = Column(Integer, nullable=False)
    hint_level = Column(String, nullable=False, default=HintLevelEnum.NO_HINTS.value)


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String, nullable=True)
    task = Column(JSON, nullable=False)  # Reference automaton structure
    
    # Relationship
    submissions = relationship("Submission", back_populates="task")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    
    # Relationship
    submissions = relationship("Submission", back_populates="user")


class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submitted_task = Column(JSON, nullable=False)  # Student automaton structure
    errors = Column(JSON, nullable=True)  # Verification errors
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="submissions")
    user = relationship("User", back_populates="submissions")
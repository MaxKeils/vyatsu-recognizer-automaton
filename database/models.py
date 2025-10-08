"""Database models for automaton application."""
from sqlalchemy import Column, String, Integer, JSON, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database.database import Base


class DifficultyModeEnum(str, enum.Enum):
    HARD_MODE = "HARD_MODE"
    MEDIUM_MODE = "MEDIUM_MODE"
    EASY_MODE = "EASY_MODE"


class Configuration(Base):
    __tablename__ = "configuration"
    
    id = Column(Integer, primary_key=True, default=1)
    duration = Column(Integer, nullable=False)
    difficulty_mode = Column(String, nullable=False, default=DifficultyModeEnum.HARD_MODE.value)
    password_hash = Column(String, nullable=True)  # SHA256 хеш пароля администратора


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String, nullable=True)
    task = Column(JSON, nullable=False)  # Reference automaton structure
    
    # Relationships
    submissions = relationship("Submission", back_populates="task")
    progress = relationship("StudentProgress", back_populates="task")
    virtual_variants = relationship("VirtualVariant", back_populates="task")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    group_name = Column(String, nullable=True)
    
    # Relationships
    submissions = relationship("Submission", back_populates="user")
    progress = relationship("StudentProgress", back_populates="user")


class StudentProgress(Base):
    __tablename__ = "student_progress"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    current_section = Column(Integer, nullable=False, default=1)
    section_1_data = Column(JSON, nullable=True)  # states, initial_state
    section_2_data = Column(JSON, nullable=True)  # transitions
    section_3_data = Column(JSON, nullable=True)  # y_equation
    is_completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="progress")
    task = relationship("Task", back_populates="progress")
    submissions = relationship("Submission", back_populates="progress")


class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    progress_id = Column(Integer, ForeignKey("student_progress.id"), nullable=True)
    section_number = Column(Integer, nullable=True)  # Номер секции (1, 2, 3)
    difficulty_mode = Column(String, nullable=True)
    is_test = Column(Boolean, nullable=False, default=False)  # Для будущего функционала тестов
    submitted_task = Column(JSON, nullable=False)  # Student automaton structure
    errors = Column(JSON, nullable=True)  # Verification errors
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", back_populates="submissions")
    user = relationship("User", back_populates="submissions")
    progress = relationship("StudentProgress", back_populates="submissions")


class VirtualVariant(Base):
    __tablename__ = "virtual_variants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    real_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    display_number = Column(Integer, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    
    # Relationship
    task = relationship("Task", back_populates="virtual_variants")
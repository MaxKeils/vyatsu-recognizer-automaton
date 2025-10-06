"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from database.models import HintLevelEnum


class ConfigurationRequest(BaseModel):
    duration: int
    hint_level: HintLevelEnum


class ConfigurationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    duration: int
    hint_level: HintLevelEnum


class TaskRequest(BaseModel):
    description: str
    task: Dict[str, Any]  # Reference automaton JSON structure


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    description: str
    task: Dict[str, Any]


class UserRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    full_name: str
    email: str


class SubmissionRequest(BaseModel):
    task_id: int
    user_id: int
    submitted_task: Dict[str, Any]  # Student automaton JSON structure


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_id: int
    user_id: int
    submitted_task: Dict[str, Any]
    errors: Optional[Dict[str, Any]]
    created_at: datetime
    
    # Optional nested objects
    task: Optional[TaskResponse] = None
    user: Optional[UserResponse] = None


class ErrorsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    submission_id: int
    errors: Optional[Dict[str, Any]]
"""API routes for task management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from database.crud import TaskCRUD
from database.schemas import TaskRequest, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=List[TaskResponse])
def get_all_tasks(db: Session = Depends(get_db)):
    """Get all available tasks."""
    tasks = TaskCRUD.get_all_tasks(db)
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_by_id(task_id: int, db: Session = Depends(get_db)):
    """Get task by ID."""
    task = TaskCRUD.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Задание не найдено"
        )
    return task


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(task_data: TaskRequest, db: Session = Depends(get_db)):
    """Create a new task."""
    task = TaskCRUD.create_task(db, task_data)
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_data: TaskRequest,
    db: Session = Depends(get_db)
):
    """Update an existing task."""
    task = TaskCRUD.update_task(db, task_id, task_data)
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Задание не найдено"
        )
    return task


@router.delete("/{task_id}", status_code=200)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task."""
    success = TaskCRUD.delete_task(db, task_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Задание не найдено"
        )
    return {
        "success": True,
        "message": "Задание успешно удалено"
    }
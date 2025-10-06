"""API эндпоинты для работы со студентами (пример)."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.database import get_db
from database.crud import StudentCRUD
from models.student import StudentCreate, StudentUpdate, StudentResponse, StudentListResponse

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """
    Создать нового студента.
    
    Args:
        student: Данные студента
        db: Сессия БД
        
    Returns:
        Созданный студент
    """
    # Проверяем, что email уникален
    if student.email:
        existing = StudentCRUD.get_by_email(db, student.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Студент с email {student.email} уже существует"
            )
    
    new_student = StudentCRUD.create(
        db=db,
        name=student.name,
        group=student.group,
        email=student.email
    )
    return new_student
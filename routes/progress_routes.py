"""API роутер для прогресса студентов."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from database.crud import StudentProgressCRUD, VirtualVariantCRUD, TaskCRUD
from database.schemas import StudentProgressResponse, VirtualVariantResponse


router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/{user_id}", response_model=List[StudentProgressResponse])
async def get_student_progress(
    user_id: int,
    db: Session = Depends(get_db)
) -> List[StudentProgressResponse]:
    """
    Получить весь прогресс студента по всем заданиям.
    
    Args:
        user_id: ID студента
        db: Сессия БД
        
    Returns:
        Список прогресса по заданиям
    """
    progress_list = StudentProgressCRUD.get_user_progress(db, user_id)
    return progress_list


@router.get("/{user_id}/task/{task_id}", response_model=StudentProgressResponse)
async def get_student_progress_for_task(
    user_id: int,
    task_id: int,
    db: Session = Depends(get_db)
) -> StudentProgressResponse:
    """
    Получить прогресс студента по конкретному заданию.
    
    Args:
        user_id: ID студента
        task_id: ID задания
        db: Сессия БД
        
    Returns:
        Прогресс по заданию
        
    Raises:
        HTTPException: Если прогресс не найден
    """
    progress = StudentProgressCRUD.get_progress(db, user_id, task_id)
    if not progress:
        raise HTTPException(
            status_code=404,
            detail="Прогресс не найден"
        )
    return progress


router_variants = APIRouter(prefix="/variants", tags=["variants"])


@router_variants.get("/", response_model=List[VirtualVariantResponse])
async def get_virtual_variants(
    db: Session = Depends(get_db)
) -> List[VirtualVariantResponse]:
    """
    Получить список всех виртуальных вариантов для отображения студентам.
    
    Виртуальные варианты создаются на основе реальных заданий,
    но их количество больше для создания иллюзии большего числа вариантов.
    
    Args:
        db: Сессия БД
        
    Returns:
        Список виртуальных вариантов с номерами для отображения
    """
    virtual_variants = VirtualVariantCRUD.get_all_virtual_variants(db)
    
    # Преобразуем в response model с описанием из реального задания
    result = []
    for vv in virtual_variants:
        task = TaskCRUD.get_task_by_id(db, vv.real_task_id)
        result.append({
            "display_number": vv.display_number,
            "description": task.description if task else None
        })
    
    return result


# Автогенерация вариантов убрана - используйте CRUD в /api/admin/variants

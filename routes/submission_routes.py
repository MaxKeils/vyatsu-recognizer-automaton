"""API routes for submission management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from collections import defaultdict
from database.database import get_db
from database.crud import SubmissionCRUD, UserCRUD, TaskCRUD
from database.schemas import (
    SubmissionRequest, SubmissionResponse, ErrorsResponse
)
from service.automaton_service import AutomatonService

router = APIRouter(prefix="/submissions", tags=["submissions"])


def group_errors_by_section(submissions: List[Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Группирует ошибки из submissions по section_number.
    Возвращает ТОЛЬКО неуспешные попытки (где success = false).
    
    Args:
        submissions: Список submission объектов
        
    Returns:
        Dict с ключами вида "section_1_errors", "section_2_errors", и т.д.
        Каждый ключ содержит список ТОЛЬКО неуспешных попыток для этой секции.
    """
    grouped = defaultdict(list)
    
    for submission in submissions:
        if submission.errors and isinstance(submission.errors, dict):
            # Фильтруем только неуспешные попытки
            if submission.errors.get("success") is False:
                section_key = f"section_{submission.section_number}_errors"
                grouped[section_key].append({
                    "submission_id": submission.id,
                    "task_id": submission.task_id,
                    "created_at": submission.created_at.isoformat() if submission.created_at else None,
                    "errors": submission.errors
                })
    
    return dict(grouped)


@router.get("/user/{user_id}")
def get_user_submissions(
    user_id: int,
    group_by_section: bool = False,
    db: Session = Depends(get_db)
):
    """
    Получить все submissions пользователя.
    
    Args:
        user_id: ID пользователя
        group_by_section: Если True, группирует ТОЛЬКО ошибочные попытки по секциям (success=false)
        db: Сессия БД
        
    Returns:
        Если group_by_section=False: List[SubmissionResponse] (все submissions)
        Если group_by_section=True: Dict с группировкой ТОЛЬКО ошибочных попыток по секциям
        
    Examples:
        GET /user/1 -> [{"id": 1, "errors": {...}}, ...]
        GET /user/1?group_by_section=true -> {
            "user_id": 1,
            "section_1_errors": [...],  # Только попытки с success=false
            "section_2_errors": [...]
        }
    """
    try:
        user = UserCRUD.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        submissions = SubmissionCRUD.get_submissions_by_user_id(db, user_id)
        
        # Если нужна группировка по секциям (только ошибочные попытки)
        if group_by_section:
            grouped_errors = group_errors_by_section(submissions)
            return {
                "user_id": user_id,
                **grouped_errors
            }
        
        # Иначе возвращаем обычный список (все submissions)
        return submissions
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Error getting user submissions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при получении submissions. Обратитесь к администратору."
        )


@router.get("/{submission_id}", response_model=SubmissionResponse)
def get_submission_by_id(submission_id: int, db: Session = Depends(get_db)):
    submission = SubmissionCRUD.get_submission_by_id(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


@router.get("/{submission_id}/errors", response_model=ErrorsResponse)
def get_submission_errors(submission_id: int, db: Session = Depends(get_db)):
    submission = SubmissionCRUD.get_submission_by_id(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return ErrorsResponse(
        submission_id=submission_id,
        errors=submission.errors
    )


@router.post("/", response_model=SubmissionResponse)
def create_submission(submission: SubmissionRequest, db: Session = Depends(get_db)):
    """
    Создать новый submission.
    
    Args:
        submission: Данные submission'а
        db: Сессия БД
        
    Returns:
        Созданный submission
    """
    try:
        # Проверяем существование пользователя и задачи
        user = UserCRUD.get_user_by_id(db, submission.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        task = TaskCRUD.get_task_by_id(db, submission.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Задание не найдено")
        
        # Создаем submission
        new_submission = SubmissionCRUD.create_submission(db, submission)
        return new_submission
    
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Error creating submission: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ошибка при создании submission. Обратитесь к администратору."
        )



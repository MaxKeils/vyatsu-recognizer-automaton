"""API роутер для автоматов."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.database import get_db
from database.crud import TaskCRUD, UserCRUD, SubmissionCRUD, ConfigurationCRUD
from database.schemas import SubmissionRequest
from models.responses import VerificationResult
from models.automaton import StudentAutomaton, ReferenceAutomaton
from service.automaton_service import AutomatonService


router = APIRouter(prefix="/automaton", tags=["automaton"])


@router.post("/verify", response_model=VerificationResult)
async def verify_automaton(
    student_automaton: StudentAutomaton,
    db: Session = Depends(get_db)
) -> VerificationResult:
    """
    Проверить автомат студента против эталонного и сохранить результат.
    
    Args:
        student_automaton: Автомат студента со всеми полями (student_id, variant, state_codes, transitions, y_equation)
        db: Сессия БД
        
    Returns:
        Результат проверки со статусом успеха и деталями ошибок
        
    Raises:
        HTTPException: Если задача или пользователь не найдены
    """

    try:
        user_id = int(student_automaton.student_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="student_id должен быть числом")
    
    user = UserCRUD.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    task = TaskCRUD.get_task_by_id(db, student_automaton.variant)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Получаем hint_level из конфигурации БД
    config = ConfigurationCRUD.get_configuration(db)
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not found")
    
    # Конвертируем hint_level из строки в int (1, 2, 3)
    hint_level_map = {
        "NO_HINTS": 1,
        "LIGHT_HINTS": 2,
        "FULL_HINTS": 3
    }
    hint_level_int = hint_level_map.get(config.hint_level, 1)
    
    try:
        # Создаем новый StudentAutomaton с hint_level из конфигурации
        student_data = student_automaton.model_dump()
        student_data['hint_level'] = hint_level_int
        student_automaton_with_hints = StudentAutomaton(**student_data)
        
        # Добавляем необходимые поля для ReferenceAutomaton
        reference_data = task.task.copy()
        
        reference_data['state_codes'] = reference_data.pop('state_codes')
        
        reference_data['variant'] = student_automaton.variant
        reference_data['description'] = task.description or f"Task {student_automaton.variant}"
        reference_automaton = ReferenceAutomaton(**reference_data)
        
        # Проверяем автомат с hint_level из конфигурации
        verification_result = AutomatonService.verify_automaton(
            student=student_automaton_with_hints,
            reference=reference_automaton,
            test_length=5
        )
        
        # Сохраняем submission в БД
        # Преобразуем StudentAutomaton в словарь для сохранения
        submitted_task_dict = student_automaton.model_dump()
        
        submission_data = SubmissionRequest(
            task_id=student_automaton.variant,
            user_id=user_id,
            submitted_task=submitted_task_dict
        )
        submission = SubmissionCRUD.create_submission(db, submission_data)
        
        # Обновляем submission с результатами проверки
        errors_data = {
            "success": verification_result.success,
            "message": verification_result.message,
            "errors": verification_result.errors,
            "test_sequences_count": verification_result.test_sequences_count
        }
        SubmissionCRUD.update_submission_errors(db, submission.id, errors_data)
        
        return verification_result
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")
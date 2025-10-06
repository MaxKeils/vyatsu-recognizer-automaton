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
        # Создаем ReferenceAutomaton
        reference_data = task.task.copy()
        reference_data['state_codes'] = reference_data.pop('state_codes')
        reference_data['variant'] = student_automaton.variant
        reference_data['description'] = task.description or f"Task {student_automaton.variant}"
        reference_automaton = ReferenceAutomaton(**reference_data)
        
        # 1. Проверяем автомат с hint_level из конфигурации (для ответа пользователю)
        student_data_for_user = student_automaton.model_dump()
        student_data_for_user['hint_level'] = hint_level_int
        student_automaton_with_user_hints = StudentAutomaton(**student_data_for_user)
        
        verification_result_for_user = AutomatonService.verify_automaton(
            student=student_automaton_with_user_hints,
            reference=reference_automaton,
            test_length=5
        )
        
        # 2. Проверяем автомат с FULL_HINTS (уровень 3) для сохранения в БД
        student_data_for_db = student_automaton.model_dump()
        student_data_for_db['hint_level'] = 3  # FULL_HINTS
        student_automaton_with_full_hints = StudentAutomaton(**student_data_for_db)
        
        verification_result_for_db = AutomatonService.verify_automaton(
            student=student_automaton_with_full_hints,
            reference=reference_automaton,
            test_length=5
        )
        
        # Сохраняем submission в БД
        submitted_task_dict = student_automaton.model_dump()
        
        submission_data = SubmissionRequest(
            task_id=student_automaton.variant,
            user_id=user_id,
            submitted_task=submitted_task_dict
        )
        submission = SubmissionCRUD.create_submission(db, submission_data)
        
        # Обновляем submission с ПОЛНЫМИ результатами проверки (FULL_HINTS)
        errors_data = {
            "success": verification_result_for_db.success,
            "message": verification_result_for_db.message,
            "errors": verification_result_for_db.errors,  # Полная информация
            "test_sequences_count": verification_result_for_db.test_sequences_count
        }
        SubmissionCRUD.update_submission_errors(db, submission.id, errors_data)
        
        # Возвращаем пользователю результат с его уровнем подсказок
        return verification_result_for_user
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")
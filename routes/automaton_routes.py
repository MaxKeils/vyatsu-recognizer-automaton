"""API роутер для автоматов."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from database.database import get_db
from database.crud import (
    TaskCRUD, UserCRUD, SubmissionCRUD, ConfigurationCRUD,
    StudentProgressCRUD, VirtualVariantCRUD
)
from database.schemas import SubmissionRequest, SectionVerificationRequest
from models.responses import VerificationResult
from models.automaton import StudentAutomaton, ReferenceAutomaton
from service.automaton_service import AutomatonService
from service.section_verification_service import SectionVerificationService


router = APIRouter(prefix="/automaton", tags=["automaton"])


@router.post("/verify", response_model=VerificationResult)
async def verify_automaton(
    student_automaton: StudentAutomaton,
    db: Session = Depends(get_db)
) -> VerificationResult:
    """
    Проверить автомат студента против эталонного и сохранить результат.
    
    Args:
        student_automaton: Автомат студента со всеми полями (student_id, variant - номер виртуального варианта, state_codes, transitions, y_equation)
        db: Сессия БД
        
    Returns:
        Результат проверки со статусом успеха и деталями ошибок
        
    Raises:
        HTTPException: Если виртуальный вариант, задача или пользователь не найдены
    """

    try:
        user_id = int(student_automaton.student_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="student_id должен быть числом")
    
    user = UserCRUD.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Получаем реальное задание через виртуальный вариант
    task = VirtualVariantCRUD.get_task_by_virtual_variant(db, student_automaton.variant)
    if not task:
        raise HTTPException(status_code=404, detail="Virtual variant not found")
    
    # Получаем difficulty_mode из конфигурации БД
    config = ConfigurationCRUD.get_configuration(db)
    if not config:
        raise HTTPException(status_code=500, detail="Configuration not found")
    
    # Конвертируем difficulty_mode в числовое значение (1, 2, 3)
    difficulty_to_int_map = {
        "HARD_MODE": 1,      # HARD_MODE
        "MEDIUM_MODE": 2,    # MEDIUM_MODE  
        "EASY_MODE": 3       # EASY_MODE
    }
    difficulty_mode_int = difficulty_to_int_map.get(config.difficulty_mode, 1)
    
    try:
        # Создаем ReferenceAutomaton
        reference_data = task.task.copy()
        reference_data['state_codes'] = reference_data.pop('state_codes')
        reference_data['variant'] = student_automaton.variant
        reference_data['description'] = task.description or f"Variant {student_automaton.variant}"
        reference_automaton = ReferenceAutomaton(**reference_data)
        
        # 1. Проверяем автомат с difficulty_mode из конфигурации (для ответа пользователю)
        student_data_for_user = student_automaton.model_dump()
        student_data_for_user['difficulty_mode'] = difficulty_mode_int
        student_automaton_with_user_hints = StudentAutomaton(**student_data_for_user)
        
        verification_result_for_user = AutomatonService.verify_automaton(
            student=student_automaton_with_user_hints,
            reference=reference_automaton,
            test_length=5
        )
        
        # 2. Проверяем автомат с EASY_MODE (уровень 3) для сохранения в БД
        student_data_for_db = student_automaton.model_dump()
        student_data_for_db['difficulty_mode'] = 3  # EASY_MODE
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
            "hints": verification_result_for_db.hints if verification_result_for_db.hints else []
        }
        SubmissionCRUD.update_submission_errors(db, submission.id, errors_data)
        
        # Возвращаем пользователю результат с его уровнем подсказок
        return verification_result_for_user
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")


@router.post("/verify-section", response_model=VerificationResult)
async def verify_section(
    request: SectionVerificationRequest,
    db: Session = Depends(get_db)
) -> VerificationResult:
    """
    Проверить конкретную секцию автомата студента используя AutomatonService.
    
    Секции:
    1. Состояния (state_codes, initial_state)
    2. Переходы (transitions) - проверяет граф
    3. Y-уравнение (y) - проверяет выходную функцию
    
    Args:
        request: Запрос с данными секции (включая virtual_variant_id)
        db: Сессия БД
        
    Returns:
        VerificationResult с ошибками и подсказками
        
    Raises:
        HTTPException: Если пользователь, виртуальный вариант или задание не найдены
    """
    # Проверяем пользователя
    user = UserCRUD.get_user_by_id(db, request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Получаем конфигурацию
    config = ConfigurationCRUD.get_configuration(db)
    if not config:
        raise HTTPException(status_code=500, detail="Конфигурация не найдена")
    
    # Конвертируем difficulty_mode в числовое значение
    difficulty_to_int_map = {
        "HARD_MODE": 1,      # HARD_MODE
        "MEDIUM_MODE": 2,    # MEDIUM_MODE  
        "EASY_MODE": 3       # EASY_MODE
    }
    difficulty_mode_int = difficulty_to_int_map.get(config.difficulty_mode, 1)
    
    # Получаем реальное задание через виртуальный вариант
    task = VirtualVariantCRUD.get_task_by_virtual_variant(db, request.virtual_variant_id)
    if not task:
        raise HTTPException(status_code=404, detail="Виртуальный вариант не найден")
    
    try:
        # Создаем ReferenceAutomaton из задания
        reference_data = task.task.copy()
        reference_data['variant'] = request.virtual_variant_id
        reference_data['description'] = task.description or f"Variant {request.virtual_variant_id}"
        reference_automaton = ReferenceAutomaton(**reference_data)
        
        # Для разных секций проверяем разные части автомата
        if request.section_number == 1:
            # Секция 1: только состояния - НЕ создаем StudentAutomaton
            # Просто проверяем базовые правила
            errors = []
            hints = []
            
            # Проверка количества состояний
            if len(request.data.state_codes) != len(reference_automaton.state_codes):
                errors.append("Неверное количество состояний")
                if difficulty_mode_int >= 2:
                    hints.append(f"Ожидается {len(reference_automaton.state_codes)} состояний, получено {len(request.data.state_codes)}")
            
            # Проверка начального состояния (по позиции, не по значению)
            ref_initial_index = reference_automaton.state_codes.index(reference_automaton.initial_state) if reference_automaton.initial_state in reference_automaton.state_codes else -1
            stud_initial_index = request.data.state_codes.index(request.data.initial_state) if request.data.initial_state in request.data.state_codes else -1
            
            if ref_initial_index != stud_initial_index:
                errors.append("Неверное начальное состояние")
                if difficulty_mode_int >= 2:
                    hints.append(f"Начальное состояние должно быть на позиции {ref_initial_index}")
            
            return VerificationResult(
                success=len(errors) == 0,
                message="Секция 1 проверена успешно" if len(errors) == 0 else "Секция 1 содержит ошибки",
                errors=errors,
                hints=hints if difficulty_mode_int >= 2 and hints else None
            )
            
        elif request.section_number == 2:
            # Секция 2: состояния + переходы (проверка графа)
            if not request.data.transitions:
                raise HTTPException(status_code=400, detail="Для секции 2 требуется поле transitions")
            
            # Создаем StudentAutomaton с фиктивным y (для секции 2 не проверяем y)
            # Используем первое состояние + первый вход как заглушку
            dummy_y = [f"{request.data.state_codes[0]}00"] if request.data.state_codes else ["0000"]
            student_data = {
                "student_id": str(request.user_id),
                "variant": request.virtual_variant_id,
                "difficulty_mode": difficulty_mode_int,
                "state_codes": request.data.state_codes or [],
                "initial_state": request.data.initial_state or "",
                "transitions": request.data.transitions or [],
                "y": dummy_y  # Фиктивное значение для валидации модели
            }
            student = StudentAutomaton(**student_data)
            
            # Используем метод verify_automaton но анализируем только граф
            result = AutomatonService.verify_automaton(
                student=student,
                reference=reference_automaton,
                test_length=3  # Короче для секции
            )
            
            # Фильтруем только ошибки графа (не Y-уравнения)
            graph_errors = [e for e in result.errors if "Y-уравнение" not in e and "уравнение" not in e.lower()]
            graph_hints = result.hints if result.hints else None
            
            return VerificationResult(
                success=len(graph_errors) == 0,
                message="Секция 2 проверена успешно" if len(graph_errors) == 0 else "Секция 2 содержит ошибки",
                errors=graph_errors,
                hints=graph_hints
            )
            
        elif request.section_number == 3:
            # Секция 3: полная проверка (граф + Y-уравнение)
            if not request.data.y_equation:
                raise HTTPException(status_code=400, detail="Для секции 3 требуется поле y_equation")
            
            # Создаем полный StudentAutomaton
            student_data = {
                "student_id": str(request.user_id),
                "variant": request.virtual_variant_id,
                "difficulty_mode": difficulty_mode_int,
                "state_codes": request.data.state_codes or [],
                "initial_state": request.data.initial_state or "",
                "transitions": request.data.transitions or [],
                "y": request.data.y_equation or []
            }
            student = StudentAutomaton(**student_data)
            
            # Полная проверка автомата
            result = AutomatonService.verify_automaton(
                student=student,
                reference=reference_automaton,
                test_length=5
            )
            
            return result
            
        else:
            raise HTTPException(status_code=422, detail="Номер секции должен быть от 1 до 3")
            
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка проверки: {str(e)}")
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
        # Безопасно возвращаем ошибки валидации данных
        raise HTTPException(status_code=422, detail="Некорректные данные в запросе")
    except HTTPException:
        # Пробрасываем уже отформатированные HTTP ошибки
        raise
    except Exception as e:
        # Логируем internal error, но не отдаем детали клиенту
        import logging
        logging.error(f"Internal error in verify_automaton: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Внутренняя ошибка при проверке автомата. Обратитесь к администратору."
        )


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
        # Получаем или создаем прогресс студента
        progress = StudentProgressCRUD.get_progress(db, request.user_id, task.id)
        if not progress:
            progress = StudentProgressCRUD.create_progress(
                db=db,
                user_id=request.user_id,
                task_id=task.id,
                difficulty_mode=config.difficulty_mode
            )
        
        # Создаем ReferenceAutomaton из задания
        reference_data = task.task.copy()
        reference_data['variant'] = request.virtual_variant_id
        reference_data['description'] = task.description or f"Variant {request.virtual_variant_id}"
        reference_automaton = ReferenceAutomaton(**reference_data)
        
        # Для разных секций проверяем разные части автомата
        if request.section_number == 1:
            # Секция 1: только состояния 
            # Проверяем базовые правила (для user's difficulty_mode)
            errors_user = []
            hints_user = []
            
            # Проверяем с полными ошибками (для БД)
            errors_full = []
            hints_full = []
            
            # Проверка количества состояний
            has_errors = False
            if len(request.data.state_codes) != len(reference_automaton.state_codes):
                has_errors = True
                # Для пользователя
                if difficulty_mode_int >= 2:
                    errors_user.append("Неверное количество состояний")
                    hints_user.append(f"Ожидается {len(reference_automaton.state_codes)} состояний, получено {len(request.data.state_codes)}")
                # Полная информация для БД
                errors_full.append("Неверное количество состояний")
                hints_full.append(f"Ожидается {len(reference_automaton.state_codes)} состояний, получено {len(request.data.state_codes)}")
            
            # Проверка начального состояния (по позиции, не по значению)
            ref_initial_index = reference_automaton.state_codes.index(reference_automaton.initial_state) if reference_automaton.initial_state in reference_automaton.state_codes else -1
            stud_initial_index = request.data.state_codes.index(request.data.initial_state) if request.data.initial_state in request.data.state_codes else -1
            
            if ref_initial_index != stud_initial_index:
                has_errors = True
                # Для пользователя
                if difficulty_mode_int >= 2:
                    errors_user.append("Неверное начальное состояние")
                    hints_user.append(f"Начальное состояние должно быть на позиции {ref_initial_index}")
                # Полная информация для БД
                errors_full.append("Неверное начальное состояние")
                hints_full.append(f"Начальное состояние должно быть на позиции {ref_initial_index}")
            
            # Сохраняем submission с полными ошибками
            section_data_dict = request.data.model_dump(exclude_none=True)
            errors_data_full = {
                "success": not has_errors,
                "message": "Секция 1 проверена успешно" if not has_errors else "Секция 1 содержит ошибки",
                "errors": errors_full,
                "hints": hints_full if hints_full else []
            }
            SubmissionCRUD.create_section_submission(
                db=db,
                task_id=request.virtual_variant_id,
                user_id=request.user_id,
                progress_id=progress.id if progress else None,
                section_number=request.section_number,
                difficulty_mode=config.difficulty_mode,
                submitted_data=section_data_dict,
                errors_data=errors_data_full
            )
            
            # ВСЕГДА сохраняем данные секции (даже при ошибке) для восстановления
            if progress:
                StudentProgressCRUD.update_section_data(
                    db=db,
                    progress_id=progress.id,
                    section_number=request.section_number,
                    section_data=section_data_dict
                )
                
                # Если успешно - увеличиваем current_section
                if not has_errors:
                    StudentProgressCRUD.increment_current_section(
                        db=db, 
                        progress_id=progress.id, 
                        section_number=request.section_number
                    )
            
            # Отдаём только первую ошибку (если есть)
            errors_to_return = errors_user[:1] if errors_user else []
            hints_to_return = hints_user[:1] if hints_user else None
            
            # Возвращаем пользователю результат с его difficulty_mode
            return VerificationResult(
                success=not has_errors,
                message="Секция 1 проверена успешно" if not has_errors else "Секция 1 содержит ошибки",
                errors=errors_to_return,
                hints=hints_to_return
            )
            
        elif request.section_number == 2:
            # Секция 2: состояния + переходы (проверка ТОЛЬКО графа, БЕЗ Y-уравнения)
            if not request.data.transitions:
                raise HTTPException(status_code=400, detail="Для секции 2 требуется поле transitions")
            
            # Создаем StudentAutomaton с фиктивным y (не используется в verify_graph_only)
            dummy_y = [f"{request.data.state_codes[0]}00"] if request.data.state_codes else ["0000"]
            
            # 1. Проверка ТОЛЬКО графа с user's difficulty_mode (для ответа пользователю)
            student_data_user = {
                "student_id": str(request.user_id),
                "variant": request.virtual_variant_id,
                "difficulty_mode": difficulty_mode_int,
                "state_codes": request.data.state_codes or [],
                "initial_state": request.data.initial_state or "",
                "transitions": request.data.transitions or [],
                "y": dummy_y
            }
            student_user = StudentAutomaton(**student_data_user)
            result_user = AutomatonService.verify_graph_only(
                student=student_user,
                reference=reference_automaton,
                test_length=3
            )
            
            # 2. Проверка ТОЛЬКО графа с EASY_MODE (для БД)
            student_data_full = {
                "student_id": str(request.user_id),
                "variant": request.virtual_variant_id,
                "difficulty_mode": 3,  # EASY_MODE
                "state_codes": request.data.state_codes or [],
                "initial_state": request.data.initial_state or "",
                "transitions": request.data.transitions or [],
                "y": dummy_y
            }
            student_full = StudentAutomaton(**student_data_full)
            result_full = AutomatonService.verify_graph_only(
                student=student_full,
                reference=reference_automaton,
                test_length=3
            )
            
            # Теперь не нужна фильтрация - verify_graph_only не проверяет Y-уравнение!
            
            # Сохраняем submission с полными ошибками
            section_data_dict = request.data.model_dump(exclude_none=True)
            errors_data_full = {
                "success": result_full.success,
                "message": "Секция 2 проверена успешно" if result_full.success else "Секция 2 содержит ошибки",
                "errors": result_full.errors,
                "hints": result_full.hints if result_full.hints else []
            }
            SubmissionCRUD.create_section_submission(
                db=db,
                task_id=request.virtual_variant_id,
                user_id=request.user_id,
                progress_id=progress.id if progress else None,
                section_number=request.section_number,
                difficulty_mode=config.difficulty_mode,
                submitted_data=section_data_dict,
                errors_data=errors_data_full
            )
            
            # ВСЕГДА сохраняем данные секции (даже при ошибке) для восстановления
            if progress:
                StudentProgressCRUD.update_section_data(
                    db=db,
                    progress_id=progress.id,
                    section_number=request.section_number,
                    section_data=section_data_dict
                )
                
                # Если успешно - увеличиваем current_section
                if result_full.success:
                    StudentProgressCRUD.increment_current_section(
                        db=db, 
                        progress_id=progress.id, 
                        section_number=request.section_number
                    )
            
            # Отдаём только первую ошибку и первую подсказку
            errors_to_return = result_user.errors[:1] if result_user.errors else []
            hints_to_return = result_user.hints[:1] if result_user.hints else None
            
            # Возвращаем пользователю результат с его difficulty_mode
            return VerificationResult(
                success=result_user.success,
                message="Секция 2 проверена успешно" if result_user.success else "Секция 2 содержит ошибки",
                errors=errors_to_return,
                hints=hints_to_return
            )
            
        elif request.section_number == 3:
            # Секция 3: полная проверка (граф + Y-уравнение)
            if not request.data.y_equation:
                raise HTTPException(status_code=400, detail="Для секции 3 требуется поле y_equation")
            
            # 1. Проверка с user's difficulty_mode (для ответа пользователю)
            student_data_user = {
                "student_id": str(request.user_id),
                "variant": request.virtual_variant_id,
                "difficulty_mode": difficulty_mode_int,
                "state_codes": request.data.state_codes or [],
                "initial_state": request.data.initial_state or "",
                "transitions": request.data.transitions or [],
                "y": request.data.y_equation or []
            }
            student_user = StudentAutomaton(**student_data_user)
            result_user = AutomatonService.verify_automaton(
                student=student_user,
                reference=reference_automaton,
                test_length=5
            )
            
            # 2. Проверка с EASY_MODE (для БД)
            student_data_full = {
                "student_id": str(request.user_id),
                "variant": request.virtual_variant_id,
                "difficulty_mode": 3,  # EASY_MODE
                "state_codes": request.data.state_codes or [],
                "initial_state": request.data.initial_state or "",
                "transitions": request.data.transitions or [],
                "y": request.data.y_equation or []
            }
            student_full = StudentAutomaton(**student_data_full)
            result_full = AutomatonService.verify_automaton(
                student=student_full,
                reference=reference_automaton,
                test_length=5
            )
            
            # Сохраняем submission с полными ошибками
            section_data_dict = request.data.model_dump(exclude_none=True)
            errors_data_full = {
                "success": result_full.success,
                "message": "Секция 3 проверена успешно. Автомат полностью корректен!" if result_full.success else "Секция 3 содержит ошибки",
                "errors": result_full.errors,
                "hints": result_full.hints if result_full.hints else []
            }
            SubmissionCRUD.create_section_submission(
                db=db,
                task_id=request.virtual_variant_id,
                user_id=request.user_id,
                progress_id=progress.id if progress else None,
                section_number=request.section_number,
                difficulty_mode=config.difficulty_mode,
                submitted_data=section_data_dict,
                errors_data=errors_data_full
            )
            
            # ВСЕГДА сохраняем данные секции (даже при ошибке) для восстановления
            if progress:
                StudentProgressCRUD.update_section_data(
                    db=db,
                    progress_id=progress.id,
                    section_number=request.section_number,
                    section_data=section_data_dict
                )
                
                # Если успешно - увеличиваем current_section и помечаем завершенным
                if result_full.success:
                    StudentProgressCRUD.increment_current_section(
                        db=db, 
                        progress_id=progress.id, 
                        section_number=request.section_number
                    )
                    StudentProgressCRUD.mark_completed(db=db, progress_id=progress.id)
            
            # Отдаём только первую ошибку и первую подсказку
            errors_to_return = result_user.errors[:1] if result_user.errors else []
            hints_to_return = result_user.hints[:1] if result_user.hints else None
            
            # Возвращаем пользователю результат с его difficulty_mode
            return VerificationResult(
                success=result_user.success,
                message="Секция 3 проверена успешно. Автомат полностью корректен!" if result_user.success else "Секция 3 содержит ошибки",
                errors=errors_to_return,
                hints=hints_to_return
            )
            
        else:
            raise HTTPException(status_code=422, detail="Номер секции должен быть от 1 до 3")
            
    except ValueError as e:
        # Безопасно возвращаем ошибки валидации
        raise HTTPException(status_code=422, detail="Некорректные данные в запросе")
    except HTTPException:
        # Пробрасываем уже отформатированные HTTP ошибки
        raise
    except Exception as e:
        # Логируем internal error, но не отдаем детали клиенту
        import logging
        logging.error(f"Internal error in verify_section: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail="Внутренняя ошибка при проверке автомата. Обратитесь к администратору."
        )
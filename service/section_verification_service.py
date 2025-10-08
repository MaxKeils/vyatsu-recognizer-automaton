"""Сервис для посекционной проверки автоматов."""
from typing import Dict, Any, List, Optional, Tuple
from database.models import DifficultyModeEnum
from models.responses import VerificationResult


class SectionVerificationService:
    """Сервис для проверки автоматов по секциям с разными режимами сложности."""
    
    @staticmethod
    def verify_section_1(
        student_states: List[str],
        student_initial: str,
        reference_states: List[str],
        reference_initial: str,
        difficulty_mode: str
    ) -> Dict[str, Any]:
        """
        Проверка секции 1: кодирование состояний.
        
        Args:
            student_states: Коды состояний студента
            student_initial: Начальное состояние студента
            reference_states: Коды состояний эталона
            reference_initial: Начальное состояние эталона
            difficulty_mode: Режим сложности (HARD_MODE, MEDIUM_MODE, EASY_MODE)
            
        Returns:
            Словарь с результатами проверки: {
                "is_correct": bool,
                "errors": List[str],
                "hints": List[str] (только для MEDIUM_MODE)
            }
        """
        errors = []
        hints = []
        
        # Проверка количества состояний
        if len(student_states) != len(reference_states):
            error_msg = f"Неверное количество состояний"
            errors.append(error_msg)
            
            if difficulty_mode == DifficultyModeEnum.MEDIUM_MODE.value:
                hints.append(
                    f"Ожидается {len(reference_states)} состояний, "
                    f"получено {len(student_states)}"
                )
        
        # Проверка длины кодирования
        if student_states and reference_states:
            student_code_len = len(student_states[0])
            reference_code_len = len(reference_states[0])
            
            if student_code_len != reference_code_len:
                error_msg = f"Неверная длина кодирования состояний"
                errors.append(error_msg)
                
                if difficulty_mode == DifficultyModeEnum.MEDIUM_MODE.value:
                    hints.append(
                        f"Длина кода состояния должна быть {reference_code_len} бит, "
                        f"получено {student_code_len}"
                    )
        
        # Проверка уникальности кодов
        if len(student_states) != len(set(student_states)):
            errors.append("Коды состояний должны быть уникальными")
            if difficulty_mode == DifficultyModeEnum.MEDIUM_MODE.value:
                hints.append("Обнаружены дублирующиеся коды состояний")
        
        # Проверка начального состояния
        if student_initial not in student_states:
            errors.append("Начальное состояние отсутствует в списке состояний")
            if difficulty_mode == DifficultyModeEnum.MEDIUM_MODE.value:
                hints.append(
                    f"Начальное состояние '{student_initial}' не найдено в списке: {student_states}"
                )
        
        # В EASY_MODE любое количество состояний разрешено
        if difficulty_mode == DifficultyModeEnum.EASY_MODE.value:
            # В легком режиме главное - правильная структура
            if student_states and student_initial in student_states:
                return {
                    "is_correct": True,
                    "errors": [],
                    "hints": []
                }
        
        is_correct = len(errors) == 0
        
        result = {
            "is_correct": is_correct,
            "errors": errors if difficulty_mode != DifficultyModeEnum.EASY_MODE.value else [],
            "hints": hints if difficulty_mode == DifficultyModeEnum.MEDIUM_MODE.value else []
        }
        
        return result
    
    @staticmethod
    def verify_section_2(
        student_transitions: List[Dict[str, Any]],
        reference_transitions: List[Dict[str, Any]],
        student_states: List[str],
        reference_states: List[str],
        difficulty_mode: str
    ) -> Dict[str, Any]:
        """
        Проверка секции 2: таблица переходов.
        
        Args:
            student_transitions: Переходы студента
            reference_transitions: Переходы эталона
            student_states: Коды состояний студента
            reference_states: Коды состояний эталона
            difficulty_mode: Режим сложности
            
        Returns:
            Словарь с результатами проверки
        """
        errors = []
        hints = []
        
        # Проверка детерминированности
        seen_transitions = {}
        for trans in student_transitions:
            from_state = trans.get("from")
            for input_signal in trans.get("on", []):
                key = (from_state, input_signal)
                if key in seen_transitions:
                    error_msg = f"Недетерминированный автомат"
                    errors.append(error_msg)
                    
                    if difficulty_mode == DifficultyModeEnum.MEDIUM_MODE.value:
                        hints.append(
                            f"Из состояния '{from_state}' по входу '{input_signal}' "
                            f"существует несколько переходов"
                        )
                    break
                seen_transitions[key] = trans
        
        # Проверка полноты таблицы переходов
        input_signals = ["00", "01", "10", "11"]
        required_transitions = len(student_states) * len(input_signals)
        actual_transitions = sum(len(t.get("on", [])) for t in student_transitions)
        
        if actual_transitions != required_transitions:
            error_msg = "Неполная таблица переходов"
            errors.append(error_msg)
            
            if difficulty_mode == DifficultyModeEnum.MEDIUM_MODE.value:
                hints.append(
                    f"Ожидается {required_transitions} переходов "
                    f"({len(student_states)} состояний × {len(input_signals)} сигналов), "
                    f"получено {actual_transitions}"
                )
        
        # Проверка существования состояний в переходах
        for trans in student_transitions:
            from_state = trans.get("from")
            to_state = trans.get("to")
            
            if from_state not in student_states:
                errors.append(f"Неизвестное состояние в переходах")
                if difficulty_mode == DifficultyModeEnum.MEDIUM_MODE.value:
                    hints.append(f"Состояние '{from_state}' не найдено в списке состояний")
                break
            
            if to_state not in student_states:
                errors.append(f"Неизвестное состояние в переходах")
                if difficulty_mode == DifficultyModeEnum.MEDIUM_MODE.value:
                    hints.append(f"Состояние '{to_state}' не найдено в списке состояний")
                break
        
        # В EASY_MODE не сравниваем с эталоном
        if difficulty_mode == DifficultyModeEnum.EASY_MODE.value:
            # В легком режиме главное - корректная структура
            if len(errors) == 0:
                return {
                    "is_correct": True,
                    "errors": [],
                    "hints": []
                }
        
        is_correct = len(errors) == 0
        
        result = {
            "is_correct": is_correct,
            "errors": errors,
            "hints": hints if difficulty_mode == DifficultyModeEnum.MEDIUM_MODE.value else []
        }
        
        return result
    
    @staticmethod
    def verify_section_3(
        student_y_equation: List[str],
        reference_y_equation: List[str],
        student_states: List[str],
        difficulty_mode: str
    ) -> Dict[str, Any]:
        """
        Проверка секции 3: уравнение Y.
        
        Args:
            student_y_equation: Уравнение Y студента
            reference_y_equation: Уравнение Y эталона
            student_states: Коды состояний студента
            difficulty_mode: Режим сложности
            
        Returns:
            Словарь с результатами проверки
        """
        errors = []
        hints = []
        
        # Проверка формата уравнения
        if not student_y_equation:
            errors.append("Уравнение Y не может быть пустым")
            return {
                "is_correct": False,
                "errors": errors,
                "hints": hints
            }
        
        state_code_len = len(student_states[0]) if student_states else 2
        expected_len = state_code_len + 2  # Код состояния + 2 бита перехода
        
        for i, eq_code in enumerate(student_y_equation):
            if len(eq_code) != expected_len:
                error_msg = "Неверный формат уравнения Y"
                errors.append(error_msg)
                
                if difficulty_mode == DifficultyModeEnum.MEDIUM_MODE.value:
                    hints.append(
                        f"Элемент {i+1}: ожидается длина {expected_len} "
                        f"(код состояния {state_code_len} битов + переход 2 бита), "
                        f"получено {len(eq_code)}"
                    )
                break
            
            # Проверка, что состояние существует
            state_part = eq_code[:state_code_len]
            if state_part not in student_states:
                error_msg = "Неверное состояние в уравнении Y"
                errors.append(error_msg)
                
                if difficulty_mode == DifficultyModeEnum.MEDIUM_MODE.value:
                    hints.append(
                        f"Состояние '{state_part}' из уравнения не найдено в списке состояний"
                    )
                break
        
        # Сравнение с эталоном
        if difficulty_mode != DifficultyModeEnum.EASY_MODE.value:
            # В HARD и MEDIUM режимах сравниваем с эталоном
            if set(student_y_equation) != set(reference_y_equation):
                error_msg = "Уравнение Y не соответствует эталону"
                errors.append(error_msg)
                
                if difficulty_mode == DifficultyModeEnum.MEDIUM_MODE.value:
                    # Находим отличия
                    missing = set(reference_y_equation) - set(student_y_equation)
                    extra = set(student_y_equation) - set(reference_y_equation)
                    
                    if missing:
                        hints.append(f"Отсутствуют элементы: {list(missing)}")
                    if extra:
                        hints.append(f"Лишние элементы: {list(extra)}")
        
        is_correct = len(errors) == 0
        
        result = {
            "is_correct": is_correct,
            "errors": errors,
            "hints": hints if difficulty_mode == DifficultyModeEnum.MEDIUM_MODE.value else []
        }
        
        return result
    
    @staticmethod
    def combine_section_data(
        section_1_data: Optional[Dict[str, Any]],
        section_2_data: Optional[Dict[str, Any]],
        section_3_data: Optional[Dict[str, Any]],
        current_section: int
    ) -> Dict[str, Any]:
        """
        Объединяет данные из предыдущих секций для проверки текущей.
        
        Args:
            section_1_data: Данные секции 1 (states, initial_state)
            section_2_data: Данные секции 2 (transitions)
            section_3_data: Данные секции 3 (y_equation)
            current_section: Номер текущей секции
            
        Returns:
            Объединенные данные всех секций
        """
        combined = {}
        
        if section_1_data:
            combined.update(section_1_data)
        
        if section_2_data and current_section >= 2:
            combined.update(section_2_data)
        
        if section_3_data and current_section >= 3:
            combined.update(section_3_data)
        
        return combined

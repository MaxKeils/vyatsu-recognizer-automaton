from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import List
from models.transition import Transition
from models.hint import HintLevel

class _BaseAutomaton(BaseModel):
    initial_state: str = Field(..., description="Начальное состояние автомата")
    state_codes: List[str] = Field(..., description="Коды состояний автомата")
    transitions: List[Transition] = Field(..., description="Список переходов автомата")
    y_equation: List[str] = Field(..., min_length=1, description="Уравнение для выхода y", examples=["0100", "1111"], alias="y")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        frozen=True,   
    )
    
    @model_validator(mode='after')
    def validate_all(self):
        self._validate_state_not_empty()
        self._validate_unique_state()
        self._validate_initial_state()
        self._validate_transitions_not_empty()
        self._validate_deterministic()
        self._validate_y_not_empty()
        self._validate_y_equation_format()
        return self
    
    def _validate_state_not_empty(self):
        if not self.state_codes:
            raise ValueError("Список состояний не может быть пустым")
        return self

    def _validate_unique_state(self):
        if len(self.state_codes) != len(set(self.state_codes)):
            raise ValueError("Состояния автомата должны быть уникальными")
    
    def _validate_initial_state(self):
        if self.initial_state not in self.state_codes:
            raise ValueError(f"Начальное состояние '{self.initial_state}' отсутствует в списке состояний: {self.state_codes}")
        
    def _validate_transitions_not_empty(self):
        if not self.transitions:
            raise ValueError("Список переходов не может быть пустым")
        return self
    
    def _validate_deterministic(self):
        """Проверка детерминированности автомата - каждая пара (состояние, вход) должна быть уникальной."""
        seen_transitions = {}  # {(from_state, input): transition_index}
        
        for idx, trans in enumerate(self.transitions):
            for input_signal in trans.on:
                key = (trans.from_state, input_signal)
                if key in seen_transitions:
                    prev_idx = seen_transitions[key]
                    prev_trans = self.transitions[prev_idx]
                    raise ValueError(
                        f"Недетерминированный автомат: из состояния '{trans.from_state}' "
                        f"по входу '{input_signal}' существует несколько переходов:\n"
                        f"  1) в состояние '{prev_trans.to_state}' с выходом {prev_trans.out}\n"
                        f"  2) в состояние '{trans.to_state}' с выходом {trans.out}"
                    )
                seen_transitions[key] = idx
        return self
        
    def _validate_y_not_empty(self):    
        if not self.y_equation:
            raise ValueError("y_equation не может быть пустым")
        return self

    def _validate_y_equation_format(self):
        state_code_len = len(self.state_codes[0])
        # Каждая строка должна иметь формат: код_состояния (state_code_len битов) + переход (2 бита)
        for i, eq_code in enumerate(self.y_equation):
            expected_len = state_code_len + 2
            if len(eq_code) != expected_len:
                raise ValueError(
                    f"y_equation[{i}]: ожидается длина {expected_len} "
                    f"(код состояния {state_code_len} битов + переход 2 бита), "
                    f"получено: '{eq_code}' длиной {len(eq_code)}"
                )
            
            # Проверка, что все символы - это 0 или 1
            if not all(c in '01' for c in eq_code):
                raise ValueError(
                    f"y_equation[{i}]: строка '{eq_code}' должна содержать только символы '0' и '1'"
                )
            
            all_codes = set(self.state_codes)
            # Извлекаем код состояния и проверяем, что он существует
            state_part = eq_code[:state_code_len]
            if state_part not in all_codes:
                raise ValueError(
                    f"y_equation[{i}]: код состояния '{state_part}' из '{eq_code}' "
                    f"отсутствует в списке кодов состояний: {self.state_codes}"
                )
        return self

    def to_dict(self):
        return self.model_dump(by_alias=True)
    
class StudentAutomaton(_BaseAutomaton):
    student_id: str = Field(..., description="Идентификатор студента")
    variant: int = Field(..., description="Номер варианта задания", ge=0)
    hint_level: HintLevel = Field(default=HintLevel.NO_HINTS, description="Уровень подсказок")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        frozen=True,
    )
    
    @model_validator(mode='after')
    def validate_all(self):
        # Вызываем валидацию базового класса
        super().validate_all()
        # Добавляем специфичные для StudentAutomaton проверки
        self._validate_student_id_not_empty()
        return self

    def _validate_student_id_not_empty(self):
        if not self.student_id or not self.student_id.strip():
            raise ValueError("student_id не может быть пустым")
        return self

class ReferenceAutomaton(_BaseAutomaton):
    variant: int = Field(..., description="Номер варианта задания", ge=0)
    description: str = Field(..., description="Описание варианта задания")
    
    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        frozen=True,
    )

    def _validate_initial_state(self):
        """Переопределяем валидацию initial_state для ReferenceAutomaton."""
        # Для ReferenceAutomaton initial_state и state_codes используют формат S0, S1, ...
        if self.initial_state not in self.state_codes:
            raise ValueError(f"Начальное состояние '{self.initial_state}' отсутствует в списке состояний: {self.state_codes}")
        return self
    
    def _validate_unique_transitions(self):
        # Проверка дубликатов по (from_state, on)
        from_on_set = set((t.from_state, tuple(t.on)) for t in self.transitions)
        if len(self.transitions) != len(from_on_set):
            raise ValueError("Переходы автомата должны быть уникальными по (from_state, on)")

        # Проверка дубликатов по (from_state, to_state)
        from_to_set = set((t.from_state, t.to_state) for t in self.transitions)
        if len(self.transitions) != len(from_to_set):
            raise ValueError("Переходы автомата должны быть уникальными по (from_state, to_state)")

    def _validate_y_equation_format(self):
        """Переопределяем валидацию y_equation для ReferenceAutomaton."""
        # Для ReferenceAutomaton y_equation использует именованные состояния (S0, S1, ...) + 2-битный вход
        for i, eq_code in enumerate(self.y_equation):
            # Проверяем, что строка начинается с S и за ней следует число и 2-битный код
            if not eq_code.startswith('S'):
                raise ValueError(
                    f"y_equation[{i}]: строка '{eq_code}' должна начинаться с 'S'"
                )
            
            # Извлекаем часть после S
            s_part = eq_code[1:]
            if len(s_part) < 3:  # минимум цифра состояния + 2 бита входа
                raise ValueError(
                    f"y_equation[{i}]: строка '{eq_code}' слишком короткая"
                )
            
            # Последние 2 символа должны быть входными битами
            input_part = s_part[-2:]
            if not all(c in '01' for c in input_part):
                raise ValueError(
                    f"y_equation[{i}]: входная часть '{input_part}' в '{eq_code}' должна содержать только '0' и '1'"
                )
            
            # Часть с номером состояния
            state_num_part = s_part[:-2]
            if not state_num_part.isdigit():
                raise ValueError(
                    f"y_equation[{i}]: номер состояния '{state_num_part}' в '{eq_code}' должен быть числом"
                )
            
            # Проверяем, что состояние существует
            state_name = f"S{state_num_part}"
            if state_name not in self.state_codes:
                raise ValueError(
                    f"y_equation[{i}]: состояние '{state_name}' из '{eq_code}' "
                    f"отсутствует в списке состояний: {self.state_codes}"
                )
        return self
    
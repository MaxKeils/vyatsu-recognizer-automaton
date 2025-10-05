from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import List
from enum import Enum

class OutputSignal(int, Enum):
    ZERO = 0
    ONE = 1

class Transition(BaseModel):
    """Модель перехода автомата."""

    from_state: str = Field(..., alias="from", description="Исходное состояние")
    to_state: str = Field(..., alias="to", description="Целевое состояние")
    on: List[str] = Field(..., description="Список входных символов, вызывающих этот переход", examples=[["00", "01"], ["10"], ["11"]])
    out: OutputSignal = Field(..., description="Выходной сигнал")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        frozen=True,
        use_enum_values=True
    )

    def __str__(self):
        return f"Transition({self.from_state} -> {self.to_state} on {self.on}, out={self.out})"

    def __repr__(self):
        return (
            f"Transition(from_state='{self.from_state}', "
            f"to_state='{self.to_state}', on={self.on}, out={self.out})"
        )

    _MAX_ON_SYMBOLS = 4  # Максимальное количество входных символов (для 1 перехода) в списке 'on'

    @model_validator(mode='after')
    def validate_all(self):
        self._validate_on_not_empty()
        self._validate_on_format()
        self._validate_max_on_length()
        self._validate_unique_on()
        return self
    
    def _validate_on_not_empty(self):
        if not self.on:
            raise ValueError(f"Список входных символов не может быть пустым")
        return self 

    def _validate_unique_on(self):
        if len(self.on) != len(set(self.on)):
            raise ValueError(f"Входные символы в переходе должны быть уникальными: {self.on}")
        return self

    def _validate_on_format(self):
        for symbol in self.on:
            if not isinstance(symbol, str) or len(symbol) != 2 or not all(c in '01' for c in symbol):
                raise ValueError(f"Каждый входной символ должен быть строкой из двух символов '0' или '1': '{symbol}'")
        return self
    
    def _validate_max_on_length(self):
        if len(self.on) > self._MAX_ON_SYMBOLS:
            raise ValueError(f"Список входных символов не может содержать более {self._MAX_ON_SYMBOLS} элементов")
        return self

    
    def to_dict(self):
        return self.model_dump(by_alias=True)
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class VerificationResult(BaseModel):
    """Результат проверки автомата."""
    
    success: bool = Field(..., description="Корректен ли автомат")
    message: str = Field(..., description="Сообщение о результате")
    errors: List[str] = Field(default_factory=list, description="Список ошибок")
    hints: Optional[List[str]] = Field(None, description="Подсказки для исправления (только в MEDIUM_MODE)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "message": "Секция 1 (состояния) проверена успешно",
                    "errors": [],
                    "hints": None
                },
                {
                    "success": False,
                    "message": "Секция 1 содержит ошибки",
                    "errors": ["Неверное количество состояний: ожидалось 3, получено 4"],
                    "hints": None
                },
                {
                    "success": False,
                    "message": "Секция 2 содержит ошибки",
                    "errors": ["Ошибка на последовательности 'ab': автомат завершился в неверном состоянии"],
                    "hints": ["Проверьте переход из состояния '0' по символу 'a'"]
                }
            ]
        }
    )
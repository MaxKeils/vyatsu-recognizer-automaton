from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

class VerificationResult(BaseModel):
    """Результат проверки автомата."""
    
    success: bool = Field(..., description="Корректен ли автомат")
    message: str = Field(..., description="Сообщение о результате")
    errors: List[str] = Field(default_factory=list, description="Список текстовых ошибок")
    test_sequences_count: int = Field(..., description="Количество проверенных тестовых последовательностей")
    state_mapping: Optional[dict] = Field(None, description="Отображение кодов студента на эталонные состояния")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Автомат верный! Все проверки пройдены.",
                "errors": [],
                "test_sequences_count": 32
            }
        }
    )
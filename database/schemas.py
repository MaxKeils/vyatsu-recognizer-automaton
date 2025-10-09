"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from database.models import DifficultyModeEnum


class ConfigurationRequest(BaseModel):
    """Запрос на обновление конфигурации системы."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "duration": 120,
                "difficulty_mode": "MEDIUM_MODE"
            }
        }
    )
    
    duration: int = Field(..., description="Длительность в минутах", ge=1)
    difficulty_mode: DifficultyModeEnum = Field(..., description="Режим сложности: HARD_MODE, MEDIUM_MODE, EASY_MODE")


class ConfigurationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    duration: int
    difficulty_mode: DifficultyModeEnum
    # password_hash не возвращаем в ответе для безопасности


class AdminLoginRequest(BaseModel):
    """Запрос на вход в админ-панель."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "password": "admin123"
            }
        }
    )
    
    password: str = Field(..., min_length=1, description="Пароль администратора")


class AdminLoginResponse(BaseModel):
    """Ответ на вход в админ-панель."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Вход выполнен успешно"
            }
        }
    )
    
    success: bool
    message: str


class AdminChangePasswordRequest(BaseModel):
    """Запрос на смену пароля администратора."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "old_password": "admin123",
                "new_password": "MyNewSecurePassword2025!"
            }
        }
    )
    
    old_password: str = Field(..., min_length=1, description="Старый пароль")
    new_password: str = Field(..., min_length=8, description="Новый пароль (минимум 8 символов)")


class TaskRequest(BaseModel):
    """
    Запрос на создание задания.
    
    ВАЖНО: В эталонном автомате состояния именуются как S0, S1, S2 и т.д.
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "description": "Автомат для распознавания последовательностей",
                "task": {
                    "initial_state": "S0",
                    "state_codes": ["S0", "S1"],
                    "transitions": [
                        {"from": "S0", "to": "S0", "on": ["00"], "out": 0},
                        {"from": "S0", "to": "S1", "on": ["11"], "out": 0},
                        {"from": "S1", "to": "S1", "on": ["11"], "out": 0},
                        {"from": "S1", "to": "S0", "on": ["00"], "out": 1}
                    ],
                    "y": ["S000", "S111"]
                }
            }
        }
    )
    
    description: str = Field(..., description="Описание задания")
    task: Dict[str, Any] = Field(
        ..., 
        description="Эталонный автомат: состояния S0, S1, ... ; переходы; y-уравнение"
    )


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    description: str


class UserRequest(BaseModel):
    """Запрос на создание/вход пользователя."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Иванов Иван Иванович",
                "group_name": "ИВТ-41"
            }
        }
    )
    
    full_name: str = Field(..., description="ФИО студента")
    group_name: Optional[str] = Field(None, description="Группа студента")


class UserUpdateRequest(BaseModel):
    """Запрос на обновление данных пользователя."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "group_name": "ИВТ-51"
            }
        }
    )
    
    full_name: Optional[str] = None
    group_name: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    full_name: str
    group_name: Optional[str] = None


class UserLoginResponse(BaseModel):
    """Ответ при входе пользователя с прогрессом."""
    user: UserResponse
    progress: Optional[List['StudentProgressResponse']] = None  # Список прогресса, если есть


class SubmissionRequest(BaseModel):
    task_id: int
    user_id: int
    submitted_task: Dict[str, Any]  # Student automaton JSON structure


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    task_id: int
    user_id: int
    submitted_task: Dict[str, Any]
    errors: Optional[Dict[str, Any]]
    created_at: datetime
    
    # Optional nested objects
    task: Optional[TaskResponse] = None
    user: Optional[UserResponse] = None


class ErrorsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    submission_id: int
    errors: Optional[Dict[str, Any]]


class SectionDataRequest(BaseModel):
    """
    Данные для проверки секции.
    
    Формат данных:
    - state_codes: коды состояний в двоичном формате (например: ["00", "01", "10"])
    - initial_state: начальное состояние в двоичном формате (например: "00")
    - transitions: список переходов с полями:
        * from: состояние-источник (двоичный код)
        * to: состояние-назначение (двоичный код)
        * on: список входных комбинаций (например: ["00", "11"])
        * out: выходной сигнал (0 или 1)
    - y_equation: список строк формата "код_состояния + вход" (например: ["0000", "0111"])
    """
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "state_codes": ["00", "01", "10"],
                    "initial_state": "00"
                },
                {
                    "state_codes": ["00", "01"],
                    "initial_state": "00",
                    "transitions": [
                        {"from": "00", "to": "00", "on": ["00"], "out": 0},
                        {"from": "00", "to": "01", "on": ["11"], "out": 0}
                    ]
                },
                {
                    "state_codes": ["00", "01"],
                    "initial_state": "00",
                    "transitions": [
                        {"from": "00", "to": "00", "on": ["00"], "out": 0},
                        {"from": "00", "to": "01", "on": ["11"], "out": 0}
                    ],
                    "y_equation": ["0000", "0111"]
                }
            ]
        }
    )
    
    # Секция 1: кодирование состояний
    state_codes: Optional[List[str]] = Field(
        None, 
        description="Коды состояний в двоичном формате (например: ['00', '01', '10'])"
    )
    initial_state: Optional[str] = Field(
        None,
        description="Начальное состояние в двоичном формате (например: '00')"
    )
    
    # Секция 2: добавляются переходы
    transitions: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Список переходов: {from: '00', to: '01', on: ['00', '11'], out: 0}"
    )
    
    # Секция 3: добавляется уравнение
    y_equation: Optional[List[str]] = Field(
        None,
        description="Y-уравнение: код_состояния + вход (например: '0000' = состояние '00' + вход '00')"
    )


class SectionVerificationRequest(BaseModel):
    """Запрос на проверку секции автомата."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": 1,
                    "virtual_variant_id": 1,
                    "section_number": 1,
                    "data": {
                        "state_codes": ["00", "01", "10"],
                        "initial_state": "00"
                    }
                },
                {
                    "user_id": 1,
                    "virtual_variant_id": 2,
                    "section_number": 2,
                    "data": {
                        "state_codes": ["00", "01"],
                        "initial_state": "00",
                        "transitions": [
                            {"from": "00", "to": "00", "on": ["00"], "out": 0},
                            {"from": "00", "to": "01", "on": ["11"], "out": 0},
                            {"from": "01", "to": "01", "on": ["11"], "out": 0},
                            {"from": "01", "to": "00", "on": ["00"], "out": 1}
                        ]
                    }
                },
                {
                    "user_id": 1,
                    "virtual_variant_id": 3,
                    "section_number": 3,
                    "data": {
                        "state_codes": ["00", "01"],
                        "initial_state": "00",
                        "transitions": [
                            {"from": "00", "to": "00", "on": ["00"], "out": 0},
                            {"from": "00", "to": "01", "on": ["11"], "out": 0}
                        ],
                        "y_equation": ["0000", "0111"]
                    }
                }
            ]
        }
    )
    
    user_id: int = Field(..., description="ID пользователя")
    virtual_variant_id: int = Field(..., description="Номер виртуального варианта (display_number), который видит студент")
    section_number: int = Field(..., ge=1, le=3, description="Номер секции: 1 - состояния, 2 - переходы, 3 - y-уравнение")
    data: SectionDataRequest = Field(..., description="Данные автомата для проверки")


class StudentProgressResponse(BaseModel):
    """Ответ с информацией о прогрессе студента."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    task_id: int
    current_section: int
    section_1_data: Optional[Dict[str, Any]] = None
    section_2_data: Optional[Dict[str, Any]] = None
    section_3_data: Optional[Dict[str, Any]] = None
    is_completed: bool
    created_at: datetime
    updated_at: datetime


class VirtualVariantResponse(BaseModel):
    """Виртуальный вариант для отображения студентам."""
    model_config = ConfigDict(from_attributes=True)
    
    display_number: int
    description: Optional[str] = None


class VirtualVariantAdminResponse(BaseModel):
    """Виртуальный вариант для админской панели (полная информация)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    real_task_id: int
    display_number: int
    created_at: datetime


class VirtualVariantCreateRequest(BaseModel):
    """Запрос на создание виртуального варианта."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "real_task_id": 1,
                "display_number": 15
            }
        }
    )
    
    real_task_id: int = Field(..., description="ID реального задания из БД")
    display_number: int = Field(..., ge=1, description="Номер варианта, который видят студенты (например: 15)")


class VirtualVariantUpdateRequest(BaseModel):
    """Запрос на обновление виртуального варианта."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "real_task_id": 2,
                "display_number": 20
            }
        }
    )
    
    real_task_id: Optional[int] = Field(None, description="Новый ID реального задания")
    display_number: Optional[int] = Field(None, ge=1, description="Новый номер для отображения")


# ============== Theory Questions Schemas ==============

class TheoryAnswerOptionBase(BaseModel):
    """Базовая схема для варианта ответа."""
    option_text: str = Field(..., description="Текст варианта ответа")
    is_correct: bool = Field(..., description="Является ли ответ правильным")
    option_order: int = Field(..., ge=1, description="Порядок отображения варианта")


class TheoryAnswerOptionCreate(TheoryAnswerOptionBase):
    """Схема для создания варианта ответа."""
    pass


class TheoryAnswerOptionResponse(TheoryAnswerOptionBase):
    """Схема ответа с вариантом ответа (для админа - с правильными ответами)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int


class TheoryAnswerOptionPublic(BaseModel):
    """Публичная схема варианта ответа (БЕЗ информации о правильности)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    option_text: str
    option_order: int


class TheoryQuestionCreate(BaseModel):
    """Схема для создания теоретического вопроса."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_text": "Что такое детерминированный конечный автомат?",
                "question_type": "single",
                "answer_options": [
                    {"option_text": "Автомат, у которого для каждого состояния и входного символа определен ровно один переход", "is_correct": True, "option_order": 1},
                    {"option_text": "Автомат, который работает случайным образом", "is_correct": False, "option_order": 2},
                    {"option_text": "Автомат с бесконечным числом состояний", "is_correct": False, "option_order": 3}
                ]
            }
        }
    )
    
    question_text: str = Field(..., description="Текст вопроса")
    question_type: str = Field(..., pattern="^(single|multiple)$", description="Тип вопроса: single или multiple")
    answer_options: List[TheoryAnswerOptionCreate] = Field(..., min_length=2, description="Варианты ответов (минимум 2)")


class TheoryQuestionUpdate(BaseModel):
    """Схема для обновления вопроса."""
    question_text: Optional[str] = Field(None, description="Новый текст вопроса")
    question_type: Optional[str] = Field(None, pattern="^(single|multiple)$", description="Новый тип вопроса")
    answer_options: Optional[List[TheoryAnswerOptionCreate]] = Field(None, description="Новые варианты ответов")


class TheoryQuestionResponse(BaseModel):
    """Схема ответа с вопросом (для админа - с правильными ответами)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    question_text: str
    question_type: str
    answer_options: List[TheoryAnswerOptionResponse]
    created_at: datetime
    updated_at: datetime


class TheoryQuestionPublic(BaseModel):
    """Публичная схема вопроса (для студентов - БЕЗ правильных ответов)."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    question_text: str
    question_type: str
    answer_options: List[TheoryAnswerOptionPublic]


class StudentAnswerRequest(BaseModel):
    """Ответ студента на один вопрос."""
    question_id: int = Field(..., description="ID вопроса")
    selected_option_ids: List[int] = Field(..., min_length=1, description="ID выбранных вариантов ответа")


class TheoryTestSubmitRequest(BaseModel):
    """Запрос на проверку теста по теории."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "answers": [
                    {"question_id": 1, "selected_option_ids": [1]},
                    {"question_id": 2, "selected_option_ids": [3, 4]}
                ]
            }
        }
    )
    
    user_id: int = Field(..., description="ID студента")
    answers: List[StudentAnswerRequest] = Field(..., min_length=1, description="Список ответов студента")


class QuestionResultDetail(BaseModel):
    """Детальный результат по одному вопросу."""
    question_id: int
    question_text: str
    question_type: str
    is_correct: bool
    selected_option_ids: List[int]
    correct_option_ids: List[int]


class TheoryTestSubmitResponse(BaseModel):
    """Ответ с результатами теста."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "total_questions": 15,
                "correct_answers": 12,
                "incorrect_answers": 3,
                "score_percentage": 80.0,
                "results": []
            }
        }
    )
    
    user_id: int
    total_questions: int
    correct_answers: int
    incorrect_answers: int
    score_percentage: float
    results: List[QuestionResultDetail]
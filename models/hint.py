from enum import Enum

# Новый класс для режимов сложности
class DifficultyMode(int, Enum):
    """Режимы сложности проверки автомата"""
    HARD_MODE = 1      # Строгая проверка, без подсказок
    MEDIUM_MODE = 2    # Проверка с подсказками
    EASY_MODE = 3      # Упрощенная проверка
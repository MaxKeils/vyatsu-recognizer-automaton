"""Репозиторий для эталонных автоматов."""
from typing import Dict, Optional
from models.automaton import ReferenceAutomaton
from models.transition import Transition


class ReferenceAutomatonRepository:
    """Хранилище эталонных автоматов в памяти."""
    
    def __init__(self):
        self._automatons: Dict[int, ReferenceAutomaton] = {}
        self._load_default_variants()
    
    def _load_default_variants(self) -> None:
        # Вариант 1: "Совпадение"
        # y = 1, когда из состояния S1 при входе x1'x2' (00)
        # Закодировано: S1 + "00" = "S100"
        variant_1 = ReferenceAutomaton(
            variant_id=1,
            description="Распознающий автомат, который выдаёт на выходе 1, если произошло совпадение (переход 11->00)",
            state_codes=["00", "01"],  # S0="00", S1="01"
            initial_state="S0",
            transitions=[
                Transition(**{"from": "S0", "to": "S0", "on": ["00", "01", "10"], "out": 0}),
                Transition(**{"from": "S0", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S0", "on": ["00"], "out": 1}),
                Transition(**{"from": "S1", "to": "S0", "on": ["01", "10"], "out": 0}),
            ],
            y_equation=["S100"]  # S1 & x1'x2'="00" (состояние S1, вход "00")
        )

        # Вариант 2: "Поглощение справа"
        # y = 1, когда из состояния S3 при входе x1'x2' (00) - нечётное количество поглощений
        # Закодировано: S3 + "00" = "S300"
        variant_2 = ReferenceAutomaton(
            variant_id=2,
            description="Распознающий автомат для поглощения справа (выдаёт 1, если было нечётное количество поглощений)",
            state_codes=["00", "01", "10", "11"],  # S0="00", S1="01", S2="10", S3="11"
            initial_state="S0",
            transitions=[
                Transition(**{"from": "S0", "to": "S0", "on": ["00", "11"], "out": 0}),
                Transition(**{"from": "S0", "to": "S1", "on": ["10"], "out": 0}),
                Transition(**{"from": "S0", "to": "S2", "on": ["01"], "out": 0}),
                Transition(**{"from": "S1", "to": "S0", "on": ["00"], "out": 0}),
                Transition(**{"from": "S1", "to": "S1", "on": ["10"], "out": 0}),
                Transition(**{"from": "S1", "to": "S2", "on": ["01"], "out": 0}),
                Transition(**{"from": "S1", "to": "S3", "on": ["11"], "out": 0}),
                Transition(**{"from": "S2", "to": "S0", "on": ["00"], "out": 0}),
                Transition(**{"from": "S2", "to": "S1", "on": ["10"], "out": 0}),
                Transition(**{"from": "S2", "to": "S2", "on": ["01"], "out": 0}),
                Transition(**{"from": "S2", "to": "S3", "on": ["11"], "out": 0}),
                Transition(**{"from": "S3", "to": "S0", "on": ["00"], "out": 1}),
                Transition(**{"from": "S3", "to": "S1", "on": ["10"], "out": 0}),
                Transition(**{"from": "S3", "to": "S2", "on": ["01"], "out": 0}),
                Transition(**{"from": "S3", "to": "S3", "on": ["11"], "out": 0}),
            ],
            y_equation=["S300"]  # S3 & x1'x2'="00" (состояние S3, вход "00")
        )

        
        self._automatons[1] = variant_1
        self._automatons[2] = variant_2
    
    def get_by_variant(self, variant: int) -> Optional[ReferenceAutomaton]:
        """Получить эталонный автомат по номеру варианта."""
        return self._automatons.get(variant)
    
    def get_all_variants(self) -> Dict[int, ReferenceAutomaton]:
        """Получить все доступные варианты."""
        return self._automatons.copy()
    
    def add_variant(self, automaton: ReferenceAutomaton) -> None:
        """Добавить или обновить вариант."""
        self._automatons[automaton.variant_id] = automaton

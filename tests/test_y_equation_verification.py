"""Тесты для проверки корректности канонического уравнения y_equation."""
import pytest
from service.automaton_service import AutomatonService
from models.automaton import (
    StudentAutomaton,
    ReferenceAutomaton
)
from models.transition import Transition


class TestYEquationVerification:
    """Тесты проверки y_equation."""
    
    def test_correct_y_equation(self):
        """Тест: правильный граф и правильное y_equation."""
        student = StudentAutomaton(
            student_id="test123",
            variant=1,
            state_codes=["0", "1"],
            initial_state="0",
            transitions=[
                Transition(**{"from": "0", "to": "0", "on": ["00", "01", "10"], "out": 0}),
                Transition(**{"from": "0", "to": "1", "on": ["11"], "out": 0}),
                Transition(**{"from": "1", "to": "1", "on": ["11"], "out": 0}),
                Transition(**{"from": "1", "to": "0", "on": ["00"], "out": 1}),
                Transition(**{"from": "1", "to": "0", "on": ["01", "10"], "out": 0}),
            ],
            y_equation=["100"]  # Правильно: состояние "1" + переход "00"
        )
        
        reference = ReferenceAutomaton(
            variant=1,
            description="Test variant",
            state_codes=["S0", "S1"],
            initial_state="S0",
            transitions=[
                Transition(**{"from": "S0", "to": "S0", "on": ["00", "01", "10"], "out": 0}),
                Transition(**{"from": "S0", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S0", "on": ["00"], "out": 1}),
                Transition(**{"from": "S1", "to": "S0", "on": ["01", "10"], "out": 0}),
            ],
            y_equation=["S100"]
        )
        
        result = AutomatonService.verify_automaton(student, reference, test_length=3)
        
        assert result.success is True
        assert "верный" in result.message.lower()
        assert len(result.errors) == 0
    
    def test_correct_graph_but_wrong_y_equation_missing_term(self):
        """Тест: граф правильный, но в y_equation не указан переход с out=1."""
        student = StudentAutomaton(
            student_id="test123",
            variant=1,
            state_codes=["0", "1"],
            initial_state="0",
            transitions=[
                Transition(**{"from": "0", "to": "0", "on": ["00", "01", "10"], "out": 0}),
                Transition(**{"from": "0", "to": "1", "on": ["11"], "out": 0}),
                Transition(**{"from": "1", "to": "1", "on": ["11"], "out": 0}),
                Transition(**{"from": "1", "to": "0", "on": ["00"], "out": 1}),  # Переход с out=1
                Transition(**{"from": "1", "to": "0", "on": ["01", "10"], "out": 0}),
            ],
            y_equation=["010"]  # НЕПРАВИЛЬНО: указан переход "0" + "10", но там out=0
        )
        
        reference = ReferenceAutomaton(
            variant=1,
            description="Test variant",
            state_codes=["S0", "S1"],
            initial_state="S0",
            transitions=[
                Transition(**{"from": "S0", "to": "S0", "on": ["00", "01", "10"], "out": 0}),
                Transition(**{"from": "S0", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S0", "on": ["00"], "out": 1}),
                Transition(**{"from": "S1", "to": "S0", "on": ["01", "10"], "out": 0}),
            ],
            y_equation=["S100"]
        )
        
        result = AutomatonService.verify_automaton(student, reference, test_length=3)
        
        assert result.success is False
        assert "граф автомата верный" in result.message.lower()
        assert "каноническое уравнение неправильное" in result.message.lower()
    
    def test_correct_graph_but_y_equation_has_extra_term(self):
        """Тест: граф правильный, но в y_equation указан лишний терм."""
        student = StudentAutomaton(
            student_id="test123",
            variant=1,
            state_codes=["0", "1"],
            initial_state="0",
            transitions=[
                Transition(**{"from": "0", "to": "0", "on": ["00", "01", "10"], "out": 0}),
                Transition(**{"from": "0", "to": "1", "on": ["11"], "out": 0}),
                Transition(**{"from": "1", "to": "1", "on": ["11"], "out": 0}),
                Transition(**{"from": "1", "to": "0", "on": ["00"], "out": 1}),  # Единственный переход с out=1
                Transition(**{"from": "1", "to": "0", "on": ["01", "10"], "out": 0}),
            ],
            y_equation=["100", "001"],  # НЕПРАВИЛЬНО: "001" лишний, там out=0
            difficulty_mode=3  # EASY_MODE - полные подсказки
        )
        
        reference = ReferenceAutomaton(
            variant=1,
            description="Test variant",
            state_codes=["S0", "S1"],
            initial_state="S0",
            transitions=[
                Transition(**{"from": "S0", "to": "S0", "on": ["00", "01", "10"], "out": 0}),
                Transition(**{"from": "S0", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S0", "on": ["00"], "out": 1}),
                Transition(**{"from": "S1", "to": "S0", "on": ["01", "10"], "out": 0}),
            ],
            y_equation=["S100"]
        )
        
        result = AutomatonService.verify_automaton(student, reference, test_length=3)
        
        assert result.success is False
        assert "граф автомата верный" in result.message.lower()
        assert "каноническое уравнение неправильное" in result.message.lower()
        errors_text = " ".join(result.errors)
        assert "не имеет выхода y=1" in errors_text.lower()
    
    def test_correct_y_equation_with_multibit_states(self):
        """Тест: правильное y_equation для автомата с 4 состояниями (2-битное кодирование)."""
        student = StudentAutomaton(
            student_id="test123",
            variant=2,
            state_codes=["00", "01", "10", "11"],
            initial_state="00",
            transitions=[
                Transition(**{"from": "00", "to": "00", "on": ["00", "11"], "out": 0}),
                Transition(**{"from": "00", "to": "01", "on": ["10"], "out": 0}),
                Transition(**{"from": "00", "to": "10", "on": ["01"], "out": 0}),
                Transition(**{"from": "01", "to": "00", "on": ["00"], "out": 0}),
                Transition(**{"from": "01", "to": "01", "on": ["10"], "out": 0}),
                Transition(**{"from": "01", "to": "10", "on": ["01"], "out": 0}),
                Transition(**{"from": "01", "to": "11", "on": ["11"], "out": 0}),
                Transition(**{"from": "10", "to": "00", "on": ["00"], "out": 0}),
                Transition(**{"from": "10", "to": "01", "on": ["10"], "out": 0}),
                Transition(**{"from": "10", "to": "10", "on": ["01"], "out": 0}),
                Transition(**{"from": "10", "to": "11", "on": ["11"], "out": 0}),
                Transition(**{"from": "11", "to": "00", "on": ["00"], "out": 1}),  # Переход с out=1
                Transition(**{"from": "11", "to": "01", "on": ["10"], "out": 0}),
                Transition(**{"from": "11", "to": "10", "on": ["01"], "out": 0}),
                Transition(**{"from": "11", "to": "11", "on": ["11"], "out": 0}),
            ],
            y_equation=["1100"]  # Правильно: состояние "11" + переход "00"
        )
        
        reference = ReferenceAutomaton(
            variant=2,
            description="Test variant",
            state_codes=["S0", "S1", "S2", "S3"],
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
            y_equation=["S300"]
        )
        
        result = AutomatonService.verify_automaton(student, reference, test_length=3)
        
        assert result.success is True
        assert "верный" in result.message.lower()
    
    def test_wrong_y_equation_with_multibit_states(self):
        """Тест: неправильное y_equation для автомата с 4 состояниями."""
        student = StudentAutomaton(
            student_id="test123",
            variant=2,
            state_codes=["00", "01", "10", "11"],
            initial_state="00",
            transitions=[
                Transition(**{"from": "00", "to": "00", "on": ["00", "11"], "out": 0}),
                Transition(**{"from": "00", "to": "01", "on": ["10"], "out": 0}),
                Transition(**{"from": "00", "to": "10", "on": ["01"], "out": 0}),
                Transition(**{"from": "01", "to": "00", "on": ["00"], "out": 0}),
                Transition(**{"from": "01", "to": "01", "on": ["10"], "out": 0}),
                Transition(**{"from": "01", "to": "10", "on": ["01"], "out": 0}),
                Transition(**{"from": "01", "to": "11", "on": ["11"], "out": 0}),
                Transition(**{"from": "10", "to": "00", "on": ["00"], "out": 0}),
                Transition(**{"from": "10", "to": "01", "on": ["10"], "out": 0}),
                Transition(**{"from": "10", "to": "10", "on": ["01"], "out": 0}),
                Transition(**{"from": "10", "to": "11", "on": ["11"], "out": 0}),
                Transition(**{"from": "11", "to": "00", "on": ["00"], "out": 1}),  # Переход с out=1
                Transition(**{"from": "11", "to": "01", "on": ["10"], "out": 0}),
                Transition(**{"from": "11", "to": "10", "on": ["01"], "out": 0}),
                Transition(**{"from": "11", "to": "11", "on": ["11"], "out": 0}),
            ],
            y_equation=["0000"],  # НЕПРАВИЛЬНО: состояние "00" + переход "00", но там out=0
            difficulty_mode=3  # EASY_MODE - полные подсказки
        )
        
        reference = ReferenceAutomaton(
            variant=2,
            description="Test variant",
            state_codes=["S0", "S1", "S2", "S3"],
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
            y_equation=["S300"]
        )
        
        result = AutomatonService.verify_automaton(student, reference, test_length=3)
        
        assert result.success is False
        assert "граф автомата верный" in result.message.lower()
        assert "каноническое уравнение неправильное" in result.message.lower()
        errors_text = " ".join(result.errors)
        assert "не имеет выхода y=1" in errors_text.lower()
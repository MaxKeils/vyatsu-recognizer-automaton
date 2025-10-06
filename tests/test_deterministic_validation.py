"""Тесты для проверки валидации детерминированности автоматов."""
import pytest
from models.automaton import StudentAutomaton, ReferenceAutomaton
from models.transition import Transition


class TestDeterministicValidation:
    """Тесты валидации детерминированности автоматов."""
    
    def test_nondeterministic_student_automaton_rejected(self):
        """Тест: недетерминированный автомат студента должен быть отклонен."""
        with pytest.raises(ValueError, match="Недетерминированный автомат"):
            StudentAutomaton(
                student_id="1",
                variant=1,
                state_codes=["00", "01"],
                initial_state="00",
                transitions=[
                    # Два перехода из "00" по входу "01"
                    Transition(**{"from": "00", "to": "00", "on": ["00", "01"], "out": 0}),
                    Transition(**{"from": "00", "to": "01", "on": ["01"], "out": 0})
                ],
                y_equation=["0000"]
            )
    
    def test_nondeterministic_reference_automaton_rejected(self):
        """Тест: недетерминированный эталонный автомат должен быть отклонен."""
        with pytest.raises(ValueError, match="Недетерминированный автомат"):
            ReferenceAutomaton(
                variant=1,
                description="Test",
                state_codes=["S0", "S1"],
                initial_state="S0",
                transitions=[
                    # Два перехода из "S0" по входу "11"
                    Transition(**{"from": "S0", "to": "S0", "on": ["00", "11"], "out": 0}),
                    Transition(**{"from": "S0", "to": "S1", "on": ["11"], "out": 0})
                ],
                y_equation=["S000"]
            )
    
    def test_deterministic_automaton_accepted(self):
        """Тест: детерминированный автомат должен быть принят."""
        # Не должно быть исключений
        student = StudentAutomaton(
            student_id="1",
            variant=1,
            state_codes=["0", "1"],
            initial_state="0",
            transitions=[
                Transition(**{"from": "0", "to": "0", "on": ["00"], "out": 0}),
                Transition(**{"from": "0", "to": "1", "on": ["11"], "out": 0}),
                Transition(**{"from": "1", "to": "1", "on": ["11"], "out": 0}),
                Transition(**{"from": "1", "to": "0", "on": ["00"], "out": 1}),
            ],
            y_equation=["100"]
        )
        assert student is not None
    
    def test_complex_nondeterministic_case(self):
        """Тест: сложный случай недетерминизма (из реального примера)."""
        with pytest.raises(ValueError, match="Недетерминированный автомат"):
            StudentAutomaton(
                student_id="1",
                variant=3,
                state_codes=["00", "01", "10", "11"],
                initial_state="00",
                transitions=[
                    # Переход 1: из "00" по "01" в "00"
                    Transition(**{"from": "00", "to": "00", "on": ["00", "01"], "out": 0}),
                    # Переход 2: из "00" по "01" в "10" - КОНФЛИКТ!
                    Transition(**{"from": "00", "to": "10", "on": ["01"], "out": 0}),
                    Transition(**{"from": "01", "to": "00", "on": ["00"], "out": 0}),
                ],
                y_equation=["0000"]
            )
    
    def test_multiple_inputs_same_transition_ok(self):
        """Тест: несколько входов в одном переходе - это нормально, если нет конфликтов."""
        student = StudentAutomaton(
            student_id="1",
            variant=1,
            state_codes=["0", "1"],
            initial_state="0",
            transitions=[
                # Один переход с несколькими входами - это OK
                Transition(**{"from": "0", "to": "0", "on": ["00", "01", "10"], "out": 0}),
                Transition(**{"from": "0", "to": "1", "on": ["11"], "out": 0}),
                Transition(**{"from": "1", "to": "0", "on": ["00"], "out": 1}),
                Transition(**{"from": "1", "to": "1", "on": ["11"], "out": 0}),
            ],
            y_equation=["100"]
        )
        assert student is not None

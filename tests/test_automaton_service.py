"""Unit tests for AutomatonService."""
import pytest
from service.automaton_service import AutomatonService
from models.automaton import (
    StudentAutomaton,
    ReferenceAutomaton
)
from models.transition import Transition


class TestAutomatonService:
    """Test cases for AutomatonService."""
    
    def test_generate_input_sequences(self):
        """Test input sequence generation."""
        # Test with length 1
        sequences = AutomatonService.generate_input_sequences(1)
        assert len(sequences) == 4  # 4^1 = 4
        assert ["00"] in sequences
        assert ["11"] in sequences
        
        # Test with length 2
        sequences = AutomatonService.generate_input_sequences(2)
        assert len(sequences) == 16  # 4^2 = 16
        assert ["00", "00"] in sequences
        assert ["11", "11"] in sequences
    
    def test_simulate_automaton_simple(self):
        """Test simulation of simple automaton."""
        # Create simple 2-state automaton: 0 -(00/0)-> 0, 0 -(11/0)-> 1, 1 -(00/1)-> 0
        transitions = [
            Transition(**{"from": "0", "to": "0", "on": ["00"], "out": 0}),
            Transition(**{"from": "0", "to": "1", "on": ["11"], "out": 0}),
            Transition(**{"from": "1", "to": "1", "on": ["11"], "out": 0}),
            Transition(**{"from": "1", "to": "0", "on": ["00"], "out": 1}),
        ]
        
        # Test sequence: 00 -> 11 -> 00
        input_seq = ["00", "11", "00"]
        outputs, states = AutomatonService.simulate_automaton(transitions, "0", input_seq)
        
        assert outputs == [0, 0, 1]
        assert states == ["0", "0", "1", "0"]
    
    def test_find_state_mapping_correct(self):
        """Test finding valid state mapping for correct automaton."""
        # Create student automaton with correct structure
        student = StudentAutomaton(
            student_id="test123",
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
        
        # Create reference automaton
        reference = ReferenceAutomaton(
            variant=1,
            description="Test variant",
            state_codes=["S0", "S1"],
            initial_state="S0",
            transitions=[
                Transition(**{"from": "S0", "to": "S0", "on": ["00"], "out": 0}),
                Transition(**{"from": "S0", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S0", "on": ["00"], "out": 1}),
            ],
            y_equation=["S100"]
        )
        
        is_valid, mapping = AutomatonService.find_state_mapping(student, reference)
        
        assert is_valid is True
        assert mapping == {"0": "S0", "1": "S1"}
    
    def test_find_state_mapping_incorrect(self):
        """Test that incorrect automaton is detected."""
        # Student has wrong output in one transition
        student = StudentAutomaton(
            student_id="test123",
            variant=1,
            state_codes=["0", "1"],
            initial_state="0",
            transitions=[
                Transition(**{"from": "0", "to": "0", "on": ["00"], "out": 0}),
                Transition(**{"from": "0", "to": "1", "on": ["11"], "out": 0}),
                Transition(**{"from": "1", "to": "1", "on": ["11"], "out": 0}),
                Transition(**{"from": "1", "to": "0", "on": ["00"], "out": 0}),  # Wrong! Should be 1
            ],
            y_equation=["100"]
        )
        
        reference = ReferenceAutomaton(
            variant=1,
            description="Test variant",
            state_codes=["S0", "S1"],
            initial_state="S0",
            transitions=[
                Transition(**{"from": "S0", "to": "S0", "on": ["00"], "out": 0}),
                Transition(**{"from": "S0", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S0", "on": ["00"], "out": 1}),
            ],
            y_equation=["S100"]
        )
        
        is_valid, mapping = AutomatonService.find_state_mapping(student, reference)
        
        assert is_valid is False
    
    def test_verify_automaton_correct(self):
        """Test verification of correct automaton."""
        student = StudentAutomaton(
            student_id="test123",
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
        
        reference = ReferenceAutomaton(
            variant=1,
            description="Test variant",
            state_codes=["S0", "S1"],
            initial_state="S0",
            transitions=[
                Transition(**{"from": "S0", "to": "S0", "on": ["00"], "out": 0}),
                Transition(**{"from": "S0", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S0", "on": ["00"], "out": 1}),
            ],
            y_equation=["S100"]
        )
        
        result = AutomatonService.verify_automaton(student, reference, test_length=3)
        
        assert result.success is True
        assert len(result.errors) == 0
    
    def test_verify_automaton_incorrect(self):
        """Test verification of incorrect automaton."""
        # Wrong output in one transition
        student = StudentAutomaton(
            student_id="test123",
            variant=1,
            state_codes=["0", "1"],
            initial_state="0",
            transitions=[
                Transition(**{"from": "0", "to": "0", "on": ["00"], "out": 0}),
                Transition(**{"from": "0", "to": "1", "on": ["11"], "out": 0}),
                Transition(**{"from": "1", "to": "1", "on": ["11"], "out": 0}),
                Transition(**{"from": "1", "to": "0", "on": ["00"], "out": 0}),  # Wrong!
            ],
            y_equation=["100"]
        )
        
        reference = ReferenceAutomaton(
            variant=1,
            description="Test variant",
            state_codes=["S0", "S1"],
            initial_state="S0",
            transitions=[
                Transition(**{"from": "S0", "to": "S0", "on": ["00"], "out": 0}),
                Transition(**{"from": "S0", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S1", "on": ["11"], "out": 0}),
                Transition(**{"from": "S1", "to": "S0", "on": ["00"], "out": 1}),
            ],
            y_equation=["S100"]
        )
        
        result = AutomatonService.verify_automaton(student, reference, test_length=3)
        
        assert result.success is False
        assert "неправильно" in result.message.lower() or "неверный" in result.message.lower()
    
    def test_verify_automaton_with_wrong_initial_state(self):
        """Test verification of automaton with incorrect initial state."""
        # Теперь валидация происходит при создании модели, поэтому проверяем, что она выбросит ошибку
        import pytest
        with pytest.raises(ValueError, match="Начальное состояние .* отсутствует в списке состояний"):
            student = StudentAutomaton(
                student_id="test123",
                variant=1,
                state_codes=["0", "1"],
                initial_state="2",  # Wrong! This state doesn't exist
                transitions=[
                    Transition(**{"from": "0", "to": "0", "on": ["00"], "out": 0}),
                    Transition(**{"from": "0", "to": "1", "on": ["11"], "out": 0}),
                    Transition(**{"from": "1", "to": "1", "on": ["11"], "out": 0}),
                    Transition(**{"from": "1", "to": "0", "on": ["00"], "out": 1}),
                ],
                y_equation=["100"]
            )
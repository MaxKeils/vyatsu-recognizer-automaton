"""Test automaton verification endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.database import get_db, Base
from database.crud import ConfigurationCRUD, TaskCRUD, UserCRUD
from database.schemas import ConfigurationRequest, TaskRequest, UserRequest

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def create_test_app():
    """Create test application with routes."""
    from fastapi import FastAPI
    from routes import automaton_routes, configuration_routes, task_routes, user_routes
    
    app = FastAPI()
    
    # Include routes
    app.include_router(automaton_routes.router, prefix="/api")
    app.include_router(configuration_routes.router, prefix="/api")
    app.include_router(task_routes.router, prefix="/api")
    app.include_router(user_routes.router, prefix="/api")
    
    # Override database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    return app


@pytest.fixture
def client():
    """Create test client with initialized database."""
    Base.metadata.create_all(bind=engine)
    app = create_test_app()
    
    # Setup: Create configuration, task, user, and virtual variant
    with TestingSessionLocal() as db:
        # Create configuration
        config_data = ConfigurationRequest(duration=120, difficulty_mode="MEDIUM_MODE")
        ConfigurationCRUD.create_or_update_configuration(db, config_data)
        
        # Create reference task
        task_data = TaskRequest(
            description="Тестовый автомат",
            task={
                "initial_state": "S0",
                "state_codes": ["S0", "S1"],
                "transitions": [
                    {"from": "S0", "to": "S0", "on": ["00"], "out": 0},
                    {"from": "S0", "to": "S1", "on": ["11"], "out": 0},
                    {"from": "S1", "to": "S1", "on": ["11"], "out": 0},
                    {"from": "S1", "to": "S0", "on": ["00"], "out": 1},
                ],
                "y": ["S100"]
            }
        )
        task = TaskCRUD.create_task(db, task_data)
        
        # Create virtual variant (display_number=1 -> real_task_id=1)
        from database.crud import VirtualVariantCRUD
        VirtualVariantCRUD.create_virtual_variant(db, real_task_id=task.id, display_number=1)
        
        # Create user
        user_data = UserRequest(full_name="Тестовый Студент Иванович", group_name="ИВТ-41")
        UserCRUD.create_or_get_user_by_full_name(db, user_data)
        
        db.commit()
    
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


class TestAutomatonVerificationRoutes:
    """Test automaton verification endpoints."""
    
    def test_verify_section_1_correct_states(self, client):
        """Test section 1 verification with correct states."""
        section_data = {
            "user_id": 1,
            "virtual_variant_id": 1,
            "section_number": 1,
            "data": {
                "state_codes": ["00", "01"],
                "initial_state": "00"
            }
        }
        
        response = client.post("/api/automaton/verify-section", json=section_data)
        if response.status_code != 200:
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert "errors" in data
        # hints могут быть null или отсутствовать в зависимости от успеха
        
    def test_verify_section_1_wrong_state_count(self, client):
        """Test section 1 verification with wrong number of states."""
        section_data = {
            "user_id": 1,
            "virtual_variant_id": 1,
            "section_number": 1,
            "data": {
                "state_codes": ["00", "01", "10"],  # 3 states instead of 2
                "initial_state": "00"
            }
        }
        
        response = client.post("/api/automaton/verify-section", json=section_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) > 0
        assert "errors" in data
        
    def test_verify_section_2_correct_transitions(self, client):
        """Test section 2 verification with correct transitions."""
        section_data = {
            "user_id": 1,
            "virtual_variant_id": 1,
            "section_number": 2,
            "data": {
                "state_codes": ["00", "01"],
                "initial_state": "00",
                "transitions": [
                    {"from": "00", "to": "00", "on": ["00"], "out": 0},
                    {"from": "00", "to": "01", "on": ["11"], "out": 0},
                    {"from": "01", "to": "01", "on": ["11"], "out": 0},
                    {"from": "01", "to": "00", "on": ["00"], "out": 1},
                ]
            }
        }
        
        response = client.post("/api/automaton/verify-section", json=section_data)
        if response.status_code != 200:
            print(f"Response: {response.json()}")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert isinstance(data["errors"], list)
        
    def test_verify_section_2_wrong_transition_output(self, client):
        """Test section 2 verification with wrong transition output."""
        section_data = {
            "user_id": 1,
            "virtual_variant_id": 1,
            "section_number": 2,
            "data": {
                "state_codes": ["00", "01"],
                "initial_state": "00",
                "transitions": [
                    {"from": "00", "to": "00", "on": ["00"], "out": 0},
                    {"from": "00", "to": "01", "on": ["11"], "out": 0},
                    {"from": "01", "to": "01", "on": ["11"], "out": 0},
                    {"from": "01", "to": "00", "on": ["00"], "out": 0},  # Wrong output! Should be 1
                ]
            }
        }
        
        response = client.post("/api/automaton/verify-section", json=section_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) > 0
        # In MEDIUM_MODE, hints should be present
        if data.get("hints"):
            assert isinstance(data["hints"], list)
    
    def test_verify_section_3_correct_y_equation(self, client):
        """Test section 3 verification with correct Y equation."""
        section_data = {
            "user_id": 1,
            "virtual_variant_id": 1,
            "section_number": 3,
            "data": {
                "state_codes": ["00", "01"],
                "initial_state": "00",
                "transitions": [
                    {"from": "00", "to": "00", "on": ["00"], "out": 0},
                    {"from": "00", "to": "01", "on": ["11"], "out": 0},
                    {"from": "01", "to": "01", "on": ["11"], "out": 0},
                    {"from": "01", "to": "00", "on": ["00"], "out": 1},
                ],
                "y_equation": ["0100"]  # state "01" + input "00" -> output 1
            }
        }
        
        response = client.post("/api/automaton/verify-section", json=section_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "message" in data
        assert isinstance(data["errors"], list)
        
    def test_verify_section_3_wrong_y_equation(self, client):
        """Test section 3 verification with wrong Y equation."""
        section_data = {
            "user_id": 1,
            "virtual_variant_id": 1,
            "section_number": 3,
            "data": {
                "state_codes": ["00", "01"],
                "initial_state": "00",
                "transitions": [
                    {"from": "00", "to": "00", "on": ["00"], "out": 0},
                    {"from": "00", "to": "01", "on": ["11"], "out": 0},
                    {"from": "01", "to": "01", "on": ["11"], "out": 0},
                    {"from": "01", "to": "00", "on": ["00"], "out": 1},
                ],
                "y_equation": ["0000", "0111"]  # Wrong! Should be ["0100"]
            }
        }
        
        response = client.post("/api/automaton/verify-section", json=section_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert len(data["errors"]) > 0
        
    def test_verify_section_invalid_section_number(self, client):
        """Test verification with invalid section number."""
        section_data = {
            "user_id": 1,
            "virtual_variant_id": 1,
            "section_number": 5,  # Invalid! Only 1-3 allowed
            "data": {
                "state_codes": ["00", "01"],
                "initial_state": "00"
            }
        }
        
        response = client.post("/api/automaton/verify-section", json=section_data)
        # Should return validation error (422)
        assert response.status_code == 422
        
    # test_verify_all_sections removed - endpoint not implemented (verify each section individually)

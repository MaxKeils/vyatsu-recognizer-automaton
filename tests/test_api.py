"""Test API endpoints for database operations."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.database import get_db, Base
from database.models import Configuration, Task, User, Submission

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
    from routes import configuration_routes, task_routes, user_routes, submission_routes
    
    app = FastAPI()
    
    # Include routes
    app.include_router(configuration_routes.router, prefix="/api/v1")
    app.include_router(task_routes.router, prefix="/api/v1")
    app.include_router(user_routes.router, prefix="/api/v1")
    app.include_router(submission_routes.router, prefix="/api/v1")
    
    # Override database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    return app


@pytest.fixture
def client():
    """Create test client."""
    Base.metadata.create_all(bind=engine)
    app = create_test_app()
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


class TestConfigurationAPI:
    """Test configuration endpoints."""

    def test_create_configuration(self, client):
        """Test creating configuration."""
        config_data = {
            "duration": 60,
            "hint_level": "LIGHT_HINTS"
        }
        
        response = client.put("/api/v1/configuration/", json=config_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["duration"] == 60
        assert data["hint_level"] == "LIGHT_HINTS"

    def test_get_configuration(self, client):
        """Test getting configuration."""
        # First create configuration
        config_data = {
            "duration": 30,
            "hint_level": "NO_HINTS"
        }
        client.put("/api/v1/configuration/", json=config_data)
        
        # Then get it
        response = client.get("/api/v1/configuration/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["duration"] == 30
        assert data["hint_level"] == "NO_HINTS"


class TestTaskAPI:
    """Test task endpoints."""

    def test_create_task(self, client):
        """Test creating a task."""
        task_data = {
            "description": "Test task",
            "task": {
                "states": ["S0", "S1"],
                "initial_state": "S0",
                "y_equation": ["S0"],
                "transitions": [
                    {
                        "from": "S0",
                        "to": "S1",
                        "on": ["01"],
                        "out": 0
                    }
                ]
            }
        }
        
        response = client.post("/api/v1/tasks/", json=task_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["description"] == "Test task"
        assert "id" in data

    def test_get_all_tasks(self, client):
        """Test getting all tasks."""
        # Create a task first
        task_data = {
            "description": "Test task",
            "task": {
                "states": ["S0", "S1"],
                "initial_state": "S0",
                "y_equation": ["S0"],
                "transitions": []
            }
        }
        client.post("/api/v1/tasks/", json=task_data)
        
        # Get all tasks
        response = client.get("/api/v1/tasks/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["description"] == "Test task"

    def test_get_task_by_id(self, client):
        """Test getting task by ID."""
        # Create a task first
        task_data = {
            "description": "Test task",
            "task": {
                "states": ["S0", "S1"],
                "initial_state": "S0",
                "y_equation": ["S0"],
                "transitions": []
            }
        }
        create_response = client.post("/api/v1/tasks/", json=task_data)
        task_id = create_response.json()["id"]
        
        # Get task by ID
        response = client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["description"] == "Test task"
        assert data["id"] == task_id


class TestUserAPI:
    """Test user endpoints."""

    def test_create_user_by_email(self, client):
        """Test creating user by email."""
        user_data = {
            "email": "test@example.com",
            "full_name": "Test User"
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert "id" in data

    def test_get_existing_user_by_email(self, client):
        """Test getting existing user by email."""
        user_data = {
            "email": "test@example.com",
            "full_name": "Test User"
        }
        
        # Create user first
        first_response = client.post("/api/v1/users/", json=user_data)
        first_user = first_response.json()
        
        # Try to create same user again
        second_response = client.post("/api/v1/users/", json=user_data)
        second_user = second_response.json()
        
        # Should return the same user
        assert first_user["id"] == second_user["id"]
        assert first_user["email"] == second_user["email"]

    def test_get_all_users(self, client):
        """Test getting all users."""
        user_data = {
            "email": "test@example.com",
            "full_name": "Test User"
        }
        client.post("/api/v1/users/", json=user_data)
        
        response = client.get("/api/v1/users/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == "test@example.com"


class TestSubmissionAPI:
    """Test submission endpoints."""

    def test_create_submission(self, client):
        """Test creating a submission."""
        # Create user first
        user_data = {
            "email": "student@example.com",
            "full_name": "Student User"
        }
        user_response = client.post("/api/v1/users/", json=user_data)
        user_id = user_response.json()["id"]
        
        # Create task first
        task_data = {
            "description": "Test task",
            "task": {
                "states": ["S0", "S1"],
                "initial_state": "S0",
                "y_equation": ["S0"],
                "transitions": [
                    {
                        "from": "S0",
                        "to": "S1",
                        "on": ["01"],
                        "out": 0
                    }
                ]
            }
        }
        task_response = client.post("/api/v1/tasks/", json=task_data)
        task_id = task_response.json()["id"]
        
        # Create submission
        submission_data = {
            "task_id": task_id,
            "user_id": user_id,
            "submitted_task": {
                "states": ["S0", "S1"],
                "initial_state": "S0",
                "y_equation": ["S0"],
                "transitions": [
                    {
                        "from": "S0",
                        "to": "S1",
                        "on": ["01"],
                        "out": 0
                    }
                ]
            }
        }
        
        response = client.post("/api/v1/submissions/", json=submission_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == task_id
        assert data["user_id"] == user_id
        assert "id" in data
        assert "errors" in data

    def test_get_user_submissions(self, client):
        """Test getting submissions by user."""
        # Create user and task first
        user_data = {
            "email": "student@example.com",
            "full_name": "Student User"
        }
        user_response = client.post("/api/v1/users/", json=user_data)
        user_id = user_response.json()["id"]
        
        task_data = {
            "description": "Test task",
            "task": {
                "states": ["S0", "S1"],
                "initial_state": "S0",
                "y_equation": ["S0"],
                "transitions": []
            }
        }
        task_response = client.post("/api/v1/tasks/", json=task_data)
        task_id = task_response.json()["id"]
        
        # Create submission
        submission_data = {
            "task_id": task_id,
            "user_id": user_id,
            "submitted_task": {
                "states": ["S0", "S1"],
                "initial_state": "S0",
                "y_equation": ["S0"],
                "transitions": []
            }
        }
        client.post("/api/v1/submissions/", json=submission_data)
        
        # Get user submissions
        response = client.get(f"/api/v1/submissions/user/{user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == user_id
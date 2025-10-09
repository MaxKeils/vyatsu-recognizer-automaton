"""Тесты для API управления виртуальными вариантами."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.database import get_db, Base
from database.crud import ConfigurationCRUD, TaskCRUD
from database.schemas import ConfigurationRequest, TaskRequest


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
    from routes import virtual_variant_routes, task_routes, configuration_routes
    
    app = FastAPI()
    
    # Include routes
    app.include_router(virtual_variant_routes.router, prefix="/api")
    app.include_router(task_routes.router, prefix="/api")
    app.include_router(configuration_routes.router, prefix="/api")
    
    # Override database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    return app


@pytest.fixture
def client():
    """Create test client with initialized database."""
    Base.metadata.create_all(bind=engine)
    app = create_test_app()
    
    # Setup: Create configuration and tasks
    with TestingSessionLocal() as db:
        # Create configuration
        config_data = ConfigurationRequest(duration=120, difficulty_mode="MEDIUM_MODE")
        ConfigurationCRUD.create_or_update_configuration(db, config_data)
        
        # Create test tasks
        task_data_1 = TaskRequest(
            description="Тестовый автомат 1",
            task={
                "initial_state": "S0",
                "state_codes": ["S0", "S1"],
                "transitions": [
                    {"from": "S0", "to": "S0", "on": ["00"], "out": 0},
                    {"from": "S0", "to": "S1", "on": ["11"], "out": 0},
                ],
                "y": ["S100"]
            }
        )
        TaskCRUD.create_task(db, task_data_1)
        
        task_data_2 = TaskRequest(
            description="Тестовый автомат 2",
            task={
                "initial_state": "S0",
                "state_codes": ["S0", "S1", "S2"],
                "transitions": [
                    {"from": "S0", "to": "S1", "on": ["00"], "out": 0},
                ],
                "y": ["S000"]
            }
        )
        TaskCRUD.create_task(db, task_data_2)
        
        db.commit()
    
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


class TestVirtualVariantAPI:
    """Тесты для API виртуальных вариантов."""
    
    def test_create_virtual_variant(self, client):
        """Тест создания виртуального варианта."""
        variant_data = {
            "real_task_id": 1,
            "display_number": 10
        }
        
        response = client.post("/api/virtual-variants/", json=variant_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["real_task_id"] == 1
        assert data["display_number"] == 10
        assert "id" in data
        assert "created_at" in data
    
    def test_create_virtual_variant_duplicate_display_number(self, client):
        """Тест создания варианта с дублирующимся display_number."""
        variant_data = {
            "real_task_id": 1,
            "display_number": 15
        }
        
        # Первое создание должно пройти
        response1 = client.post("/api/virtual-variants/", json=variant_data)
        assert response1.status_code == 201
        
        # Второе создание с тем же display_number должно вернуть 409
        response2 = client.post("/api/virtual-variants/", json=variant_data)
        assert response2.status_code == 409
        assert "уже существует" in response2.json()["detail"]
    
    def test_create_virtual_variant_nonexistent_task(self, client):
        """Тест создания варианта с несуществующим заданием."""
        variant_data = {
            "real_task_id": 999,
            "display_number": 20
        }
        
        response = client.post("/api/virtual-variants/", json=variant_data)
        assert response.status_code == 404
        assert "не найдено" in response.json()["detail"]
    
    def test_get_all_virtual_variants(self, client):
        """Тест получения всех виртуальных вариантов."""
        # Создаем несколько вариантов
        client.post("/api/virtual-variants/", json={"real_task_id": 1, "display_number": 1})
        client.post("/api/virtual-variants/", json={"real_task_id": 2, "display_number": 2})
        
        response = client.get("/api/virtual-variants/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        assert data[0]["display_number"] == 1
        assert data[1]["display_number"] == 2
    
    def test_get_virtual_variant_by_id(self, client):
        """Тест получения варианта по ID."""
        # Создаем вариант
        create_response = client.post(
            "/api/virtual-variants/",
            json={"real_task_id": 1, "display_number": 25}
        )
        variant_id = create_response.json()["id"]
        
        # Получаем его по ID
        response = client.get(f"/api/virtual-variants/{variant_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == variant_id
        assert data["display_number"] == 25
    
    def test_get_nonexistent_virtual_variant(self, client):
        """Тест получения несуществующего варианта."""
        response = client.get("/api/virtual-variants/999")
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]
    
    def test_update_virtual_variant(self, client):
        """Тест обновления виртуального варианта."""
        # Создаем вариант
        create_response = client.post(
            "/api/virtual-variants/",
            json={"real_task_id": 1, "display_number": 30}
        )
        variant_id = create_response.json()["id"]
        
        # Обновляем его
        update_data = {
            "real_task_id": 2,
            "display_number": 35
        }
        response = client.put(f"/api/virtual-variants/{variant_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["real_task_id"] == 2
        assert data["display_number"] == 35
    
    def test_update_virtual_variant_partial(self, client):
        """Тест частичного обновления виртуального варианта."""
        # Создаем вариант
        create_response = client.post(
            "/api/virtual-variants/",
            json={"real_task_id": 1, "display_number": 40}
        )
        variant_id = create_response.json()["id"]
        
        # Обновляем только display_number
        update_data = {"display_number": 45}
        response = client.put(f"/api/virtual-variants/{variant_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["real_task_id"] == 1  # Остался прежним
        assert data["display_number"] == 45  # Обновился
    
    def test_update_virtual_variant_conflict(self, client):
        """Тест обновления с конфликтом display_number."""
        # Создаем два варианта
        client.post("/api/virtual-variants/", json={"real_task_id": 1, "display_number": 50})
        create_response = client.post(
            "/api/virtual-variants/",
            json={"real_task_id": 1, "display_number": 51}
        )
        variant_id = create_response.json()["id"]
        
        # Пытаемся обновить второй вариант на display_number первого
        update_data = {"display_number": 50}
        response = client.put(f"/api/virtual-variants/{variant_id}", json=update_data)
        assert response.status_code == 409
        assert "уже существует" in response.json()["detail"]
    
    def test_update_nonexistent_virtual_variant(self, client):
        """Тест обновления несуществующего варианта."""
        update_data = {"display_number": 60}
        response = client.put("/api/virtual-variants/999", json=update_data)
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]
    
    def test_delete_virtual_variant(self, client):
        """Тест удаления виртуального варианта."""
        # Создаем вариант
        create_response = client.post(
            "/api/virtual-variants/",
            json={"real_task_id": 1, "display_number": 70}
        )
        variant_id = create_response.json()["id"]
        
        # Удаляем его
        response = client.delete(f"/api/virtual-variants/{variant_id}")
        assert response.status_code == 204
        
        # Проверяем, что он действительно удален
        get_response = client.get(f"/api/virtual-variants/{variant_id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_virtual_variant(self, client):
        """Тест удаления несуществующего варианта."""
        response = client.delete("/api/virtual-variants/999")
        assert response.status_code == 404
        assert "не найден" in response.json()["detail"]

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, engine, SessionLocal
from models import Todos

# Setup the test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[SessionLocal] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="module")
def test_client():
    with TestClient(app) as c:
        yield c

def authenticate_client(client):
    response = client.post("/auth/login", data={"username": "testuser", "password": "testpassword"})
    return response.cookies

def test_read_all_by_user(test_client):
    cookies = authenticate_client(test_client)
    response = test_client.get("/todos/", cookies=cookies)
    assert response.status_code == 200
    assert "todos" in response.text

def test_add_todo_view(test_client):
    cookies = authenticate_client(test_client)
    response = test_client.get("/todos/add-todo", cookies=cookies)
    assert response.status_code == 200
    assert "add-todo" in response.text

def test_create_todo(test_client):
    cookies = authenticate_client(test_client)
    response = test_client.post("/todos/add-todo", data={"title": "Test Todo", "description": "Test Description", "priority": 1}, cookies=cookies)
    assert response.status_code == 302
    assert response.headers["location"] == "/todos"

def test_edit_todo_view(test_client, test_db):
    new_todo = Todos(title="Test Todo", description="Test Description", priority=1, owner_id=1)
    db = next(override_get_db())
    db.add(new_todo)
    db.commit()
    cookies = authenticate_client(test_client)
    response = test_client.get(f"/todos/edit-todo/{new_todo.id}", cookies=cookies)
    assert response.status_code == 200
    assert "edit-todo" in response.text

def test_edit_todo_commit(test_client, test_db):
    new_todo = Todos(title="Test Todo", description="Test Description", priority=1, owner_id=1)
    db = next(override_get_db())
    db.add(new_todo)
    db.commit()
    cookies = authenticate_client(test_client)
    response = test_client.post(f"/todos/edit-todo/{new_todo.id}", data={"title": "Updated Todo", "description": "Updated Description", "priority": 2}, cookies=cookies)
    assert response.status_code == 302
    assert response.headers["location"] == "/todos"

def test_delete_todo(test_client, test_db):
    new_todo = Todos(title="Test Todo", description="Test Description", priority=1, owner_id=1)
    db = next(override_get_db())
    db.add(new_todo)
    db.commit()
    cookies = authenticate_client(test_client)
    response = test_client.get(f"/todos/delete/{new_todo.id}", cookies=cookies)
    assert response.status_code == 302
    assert response.headers["location"] == "/todos"

def test_complete_todo(test_client, test_db):
    new_todo = Todos(title="Test Todo", description="Test Description", priority=1, owner_id=1)
    db = next(override_get_db())
    db.add(new_todo)
    db.commit()
    cookies = authenticate_client(test_client)
    response = test_client.get(f"/todos/complete/{new_todo.id}", cookies=cookies)
    assert response.status_code == 302
    assert response.headers["location"] == "/todos"
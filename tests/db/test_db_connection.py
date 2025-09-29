from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from tests.db.test_model import TestModel


def test_database_connection(db: Session):
    """
    Test the database connection is working by executing a simple query
    """
    result = db.execute(text("SELECT 1")).scalar()
    assert result == 1


def test_create_table(db: Session):
    """
    Test that we can create a table in the database
    """
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()

    assert "test_table" in tables


def test_crud_operations(db: Session):
    """
    Test basic CRUD operations on the database
    """
    test_record = TestModel(name="test_name", value="test_value")
    db.add(test_record)
    db.commit()

    retrieved = db.query(TestModel).filter_by(name="test_name").first()
    assert retrieved is not None
    assert retrieved.value == "test_value"

    retrieved.value = "updated_value"
    db.commit()
    db.refresh(retrieved)
    assert retrieved.value == "updated_value"

    db.delete(retrieved)
    db.commit()

    check = db.query(TestModel).filter_by(name="test_name").first()
    assert check is None

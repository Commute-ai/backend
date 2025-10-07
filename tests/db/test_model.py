from sqlalchemy import Column, Integer, String

from app.db.database import Base


class SampleModel(Base):
    __tablename__ = "test_table"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    value = Column(String(100))

    def __init__(self, name, value):
        self.name = name
        self.value = value

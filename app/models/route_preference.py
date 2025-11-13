from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class RoutePreference(Base):
    __tablename__ = "route_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    prompt = Column(String, nullable=False)
    from_latitude = Column(Float, nullable=False)
    from_longitude = Column(Float, nullable=False)
    to_latitude = Column(Float, nullable=False)
    to_longitude = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="route_preferences")

    def __init__(
        self,
        user_id,
        prompt,
        from_latitude,
        from_longitude,
        to_latitude,
        to_longitude,
    ):
        self.user_id = user_id
        self.prompt = prompt
        self.from_latitude = from_latitude
        self.from_longitude = from_longitude
        self.to_latitude = to_latitude
        self.to_longitude = to_longitude

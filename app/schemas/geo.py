"""
Location and Coordinate Type Definitions

Pydantic models for representing geographic locations, coordinates,
and related data structures used throughout the application.
"""

from pydantic import BaseModel, Field, field_validator


class Coordinates(BaseModel):
    """
    Geographic coordinates (latitude and longitude).
    """

    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        """Ensure latitude is within valid range."""
        if not -90.0 <= v <= 90.0:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        """Ensure longitude is within valid range."""
        if not -180.0 <= v <= 180.0:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        return v

    def __str__(self) -> str:
        return f"({self.latitude}, {self.longitude})"

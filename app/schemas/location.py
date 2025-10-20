"""
Location Schema

Pydantic models for representing places and locations.
"""

from typing import Optional

from pydantic import BaseModel

from app.schemas.geo import Coordinates


class Place(BaseModel):
    """A place with metadata"""

    coordinates: Coordinates
    name: Optional[str] = None

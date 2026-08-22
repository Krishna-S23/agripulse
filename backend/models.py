from pydantic import BaseModel, Field
from typing import Optional


class FarmProfile(BaseModel):
    farm_id: str
    district: str
    location: Optional[str] = None
    crop: str
    area_acres: Optional[float] = None
    growth_stage: Optional[str] = None
    soil_type: Optional[str] = None
    owner_name: Optional[str] = None


class FarmCreateRequest(BaseModel):
    district: str
    location: Optional[str] = None
    crop: str
    area_acres: Optional[float] = None
    growth_stage: Optional[str] = None
    soil_type: Optional[str] = None
    owner_name: Optional[str] = None


class AskRequest(BaseModel):
    farm_id: str
    question: str = Field(..., min_length=3)

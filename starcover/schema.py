from datetime import datetime
from typing import Any,Optional
from pydantic import BaseModel, Field


class Stroke(BaseModel):
    color: str = Field(serialization_alias="stroke")
    width: Optional[float] = Field(serialization_alias="stroke_width", 
                                   ge=0, default=None)
    opacity: Optional[float] = Field(serialization_alias="stroke_opacity", 
                                     ge=0, le=1, default=None)


class Fill(BaseModel):
    color: str = Field(serialization_alias="fill")
    opacity: Optional[float] = Field(serialization_alias="fill_opacity", 
                                     ge=0, le=1, default=None)


class ElementStyle(BaseModel):
    fill: Fill
    stroke: Stroke

    # Unpack everything into a single dictionary
    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        raw = super().model_dump(*args, **kwargs)
        return {k: v for subset in raw.values() for k, v in subset.items()}

    def flat_dump(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_unset=True)


class Style(BaseModel):
    stars: ElementStyle
    constellations: ElementStyle


class Observer(BaseModel):
    datetime: datetime
    location: dict[str, float]


class Output(BaseModel):
    name: str
    max_magnitude: float
    field_of_view: float
    size: str


class Config(BaseModel):
    observer: Observer
    output: Output
    style: Style

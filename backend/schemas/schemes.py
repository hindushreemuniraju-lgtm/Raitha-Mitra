"""Government schemes schemas."""

from typing import List

from pydantic import BaseModel


class SchemeOut(BaseModel):
    id: str
    name: str
    level: str
    state: str
    category_tags: List[str]
    crop_tags: List[str]
    benefits: str
    eligibility: List[str]
    documents_required: List[str]
    application_steps: List[str]
    official_url: str
    last_verified: str
    source: str


class SchemesListOut(BaseModel):
    apisetu_status: str
    data_gov_status: str
    schemes: List[SchemeOut]

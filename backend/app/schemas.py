from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re

# Lead Email validation regex fallback just in case EmailStr needs verification
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

class EnrichRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Lead's full name")
    email: EmailStr = Field(..., description="Lead's business or personal email address")
    company: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Lead's company name")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.match(EMAIL_REGEX, value):
            raise ValueError("Invalid email format")
        return value

class EnrichResponse(BaseModel):
    linkedin_url: Optional[str] = Field(default=None, description="Enriched LinkedIn Profile URL")
    company_size: Optional[str] = Field(default=None, description="Enriched estimate of company size")
    industry: Optional[str] = Field(default=None, description="Enriched industry category")

class ClassifyRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Incoming message from the lead to classify intent")

class ClassifyResponse(BaseModel):
    intent: str = Field(..., description="Classified intent of the lead (e.g. sales_enquiry, support, spam, job_application)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score of the intent classification")

# Additional utility schemas for lead database storage representation
class LeadDBBase(BaseModel):
    name: Optional[str] = None
    email: str
    company: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    lead_message: Optional[str] = None
    intent: Optional[str] = None
    confidence: Optional[float] = None
    status: str

class LeadCreate(LeadDBBase):
    pass

class LeadResponse(LeadDBBase):
    id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
        
# Error Response Schema
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None

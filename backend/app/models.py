import uuid
from sqlalchemy import Column, String, Numeric, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import enum

from app.database import Base

class LeadStatus(str, enum.Enum):
    PENDING = "pending"
    ENRICHING = "enriching"
    ENRICHED = "enriched"
    CLASSIFYING = "classifying"
    CLASSIFIED = "classified"
    FAILED = "failed"

class Lead(Base):
    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    company = Column(String(255), nullable=True)
    
    # Enrichment fields
    linkedin_url = Column(String(500), nullable=True)
    company_size = Column(String(100), nullable=True)
    industry = Column(String(150), nullable=True)
    
    # Classification fields
    lead_message = Column(Text, nullable=True)
    intent = Column(String(100), nullable=True)
    confidence = Column(Numeric(precision=5, scale=4), nullable=True)
    
    # Status & Logging metadata
    status = Column(Enum(LeadStatus), default=LeadStatus.PENDING, nullable=False)
    raw_payload = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Lead id={self.id} email={self.email} status={self.status}>"

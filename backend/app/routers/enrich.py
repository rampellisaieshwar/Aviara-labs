from fastapi import APIRouter, HTTPException, status, Depends
import logging

from app.schemas import EnrichRequest, EnrichResponse, ErrorResponse
from app.services.enrichment import EnrichmentService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/enrich",
    tags=["Enrichment"]
)

@router.post(
    "",
    response_model=EnrichResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Input Data"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def enrich_lead(payload: EnrichRequest):
    """
    Enriches incoming lead data using email domain heuristics.
    
    Accepts lead name, email (validated), and optional company.
    Returns corporate indicators such as linkedin_url, estimated company size, and industry.
    """
    try:
        logger.info(f"Received enrichment request for email: {payload.email}")
        result = await EnrichmentService.enrich_lead(
            name=payload.name,
            email=payload.email,
            company=payload.company
        )
        return result
    except Exception as e:
        logger.exception(f"Unexpected error in /enrich router: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment service error: {str(e)}"
        )

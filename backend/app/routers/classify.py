from fastapi import APIRouter, HTTPException, status
import logging

from app.schemas import ClassifyRequest, ClassifyResponse, ErrorResponse
from app.services.groq_llm import GroqClassificationService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/classify",
    tags=["Classification"]
)

@router.post(
    "",
    response_model=ClassifyResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Input Data"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def classify_lead_message(payload: ClassifyRequest):
    """
    Classifies intent of a lead message using Groq AI Llama models.
    
    Accepts text message.
    Returns classified intent (e.g. sales_enquiry, support, spam, job_application, partnership, other)
    along with confidence score.
    """
    try:
        logger.info("Received classification request")
        if not payload.message or not payload.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message body cannot be empty"
            )
            
        result = await GroqClassificationService.classify_message(payload.message)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in /classify router: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification service error: {str(e)}"
        )

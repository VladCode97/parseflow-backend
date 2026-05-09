from fastapi import APIRouter, HTTPException
from app.presentation.api.dependencies import get_extraction_engine
from app.presentation.schemas import response_schema, request_schema

router = APIRouter()


@router.post("/processing")
async def process(request: request_schema.ProcessingRequestSchema):
    try:
        return get_extraction_engine(request)
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "DOCUMENT_PROCESSING_ERROR",
                "message": str(error),
            },
        )

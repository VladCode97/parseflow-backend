import base64
from dotenv import load_dotenv
from app.infrastructure.ocr.veryfi_provider import VeryfiProvider
import os
from app.applications.services.process_document import ProcessDocument
from app.presentation.schemas.request_schema import ProcessingRequestSchema

"""
Get the required environment variable
:param name: name of the environment variable
:return: the value of the environment variable
:rtype: str
:raises RuntimeError: if the environment variable is not set"""


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


"""
Get the extraction engine
:param body: body of the request
:return: the result of the extraction engine
:rtype: dict
:raises RuntimeError: if the required environment variables are not set
:raises ValueError: if the file is not provided in the request body
:raises ValueError: if the file is not a valid image
:raises ValueError: if the file is not a valid PDF
:raises ValueError: if the file is not a valid JPG"""


def get_extraction_engine(body: ProcessingRequestSchema):
    load_dotenv()
    verify_provider = VeryfiProvider(
        api_key=get_required_env("VERYFI_API_KEY"),
        username=get_required_env("VERYFI_USERNAME"),
        client_id=get_required_env("VERYFI_CLIENT_ID"),
        client_secret=get_required_env("VERYFI_CLIENT_SECRET"),
    )
    process_document = ProcessDocument()
    if body.document_url is not None:
        veryfi_response = verify_provider.process(
            file=str(body.document_url),
        )
        print(veryfi_response)
        return process_document.process(
            ocr_text=veryfi_response["ocr_text"],
        )
    if body.document_base64 is not None:
        veryfi_response = verify_provider.process(
            file=base64.b64decode(body.document_base64),
            filename=body.filename,
        )
        return process_document.process(
            ocr_text=veryfi_response["ocr_text"],
        )
    raise ValueError("Either document_url or document_base64 is required")

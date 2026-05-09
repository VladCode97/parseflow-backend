from pathlib import Path
from pydantic import (
    BaseModel,
    HttpUrl,
    Field,
    model_validator,
    ConfigDict,
    field_validator,
)
from typing import Optional


class ProcessingRequestSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_url: Optional[HttpUrl] = Field(
        None, description="The URL of the document to process"
    )
    document_base64: Optional[str] = Field(
        None, description="The base64 encoded document to process"
    )
    filename: Optional[str] = Field(
        None, description="The filename of the base64 document"
    )

    @field_validator("filename")
    @classmethod
    def validate_filename_extension(cls, filename: Optional[str]):
        if filename is None:
            return filename
        allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
        extension = Path(filename).suffix.lower()
        if extension not in allowed_extensions:
            raise ValueError("filename must be a PDF, JPG, PNG, DOC or DOCX file")
        return filename

    @model_validator(mode="after")
    def validate_document_source(self):
        if self.document_url is None and self.document_base64 is None:
            raise ValueError("Either document_url or document_base64 is required")
        if self.document_url is not None and self.document_base64 is not None:
            raise ValueError("Only one of document_url or document_base64 is allowed")
        if self.document_base64 is not None and self.filename is None:
            raise ValueError("filename is required when document_base64 is provided")
        return self

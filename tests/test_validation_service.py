from app.applications.use_cases.validation_service import ValidationService
from app.domain.models.extraction_result import ExtractionResult
from app.domain.models.extracted_field import ExtractedField, ExtractionSource

service = ValidationService()


def test_is_supported_document():
    text = "INVOICE\nTotal: $100\nDate: 11/02/2019"
    assert service.is_supported_document(text) == True


def test_is_unsupported_document():
    text = "Thank you for shopping at Walgreens"
    assert service.is_supported_document(text) == False


def test_validate_required_fields_with_missing():
    result = ExtractionResult(
        fields={
            "vendor_name": ExtractedField(
                value="East Repair",
                confidence=0.85,
                source=ExtractionSource.REGEX_WITHOUT_LABEL,
            ),
            "invoice_number": ExtractedField(
                value="NOT_FOUND", confidence=0.0, source=ExtractionSource.NOT_FOUND
            ),
            "date": ExtractedField(
                value="NOT_FOUND", confidence=0.0, source=ExtractionSource.NOT_FOUND
            ),
            "bill_to": ExtractedField(
                value="NOT_FOUND", confidence=0.0, source=ExtractionSource.NOT_FOUND
            ),
        },
        line_items=[],
    )
    assert service.validate_required_fields(result) == True

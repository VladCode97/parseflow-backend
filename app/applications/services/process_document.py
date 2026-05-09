from app.applications.use_cases.normalization_service import NormalizationService
from app.applications.use_cases.validation_service import ValidationService
from app.applications.use_cases.extractors.regex.regex_extractor import RegexExtractor


class ProcessDocument:

    def __init__(self):
        self.normalization_service = NormalizationService()
        self.validation_service = ValidationService()
        self.regex_extractor = RegexExtractor()

    def process(self, ocr_text: str):
        normalize_text = self.normalization_service.normalize(ocr_text)
        is_supported = self.validation_service.is_supported_document(normalize_text)
        if not is_supported:
            raise ValueError("Unsupported document type")

        extraction_result = self.regex_extractor.extract(normalize_text)
        self.validation_service.validate_required_fields(extraction_result)

        return extraction_result

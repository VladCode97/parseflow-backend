from app.applications.use_cases.normalization_service import NormalizationService
from app.applications.use_cases.validation_service import ValidationService
from app.applications.use_cases.extractors.regex.regex_extractor import RegexExtractor
from app.applications.use_cases.extractors.NPL.npl_extractor import NLPExtractor
from app.applications.use_cases.extractors.LLM.LLMExtractor import LLMExtractor


class ProcessDocument:

    def __init__(self):
        self.normalization_service = NormalizationService()
        self.validation_service = ValidationService()
        self.regex_extractor = RegexExtractor()
        self.nlp_extractor = NLPExtractor()
        self.llmExtractor = LLMExtractor()

    def process(self, ocr_text: str):
        normalize_text = self.normalization_service.normalize(ocr_text)
        is_supported = self.validation_service.is_supported_document(normalize_text)
        if not is_supported:
            raise ValueError("Unsupported document type")

        extraction_result = self.regex_extractor.extract(normalize_text)

        nltk_result = self.nlp_extractor.extract(normalize_text)
        for field_name, field_value in extraction_result.fields.items():
            if field_value.value == "NOT_FOUND":
                nltk_field = nltk_result.fields.get(field_name)
                if nltk_result and nltk_field.value != "NOT_FOUND":
                    extraction_result.fields[field_name] = nltk_field

        still_missing = [
            name
            for name, field in extraction_result.fields.items()
            if field.value == "NOT_FOUND" or field.confidence <= 0.50
        ]

        if still_missing:
            llm_result = self.llmExtractor.extract(normalize_text)
            for field_name in still_missing:
                llm_field = llm_result.fields.get(field_name)
                if llm_field and llm_field.value != "NOT_FOUND":
                    extraction_result.fields[field_name] = llm_field

        self.validation_service.validate_required_fields(extraction_result)

        return extraction_result

from app.domain.models.extraction_result import ExtractionResult


class ValidationService:
    REQUIRED_KEYWORD = ["invoice", "total", "date"]
    REQUIRED_FIELD = ["vendor_name", "invoice_number", "date", "bill_to"]

    def is_supported_document(self, text: str) -> bool:
        matches = 0
        normalize_text = text.lower()
        for keyword in self.REQUIRED_KEYWORD:
            if keyword in normalize_text:
                matches += 1
        return matches >= 2

    def validate_required_fields(self, extracted_fields: ExtractionResult) -> bool:
        missing = []
        for field in self.REQUIRED_FIELD:
            extracted_field = extracted_fields.fields.get(field)
            if not extracted_field or extracted_field.value == "NOT_FOUND":
                missing.append(field)

        if missing:
            print(f"Warning: fields not extracted: {', '.join(missing)}")

        return True

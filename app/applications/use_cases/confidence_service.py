from app.domain.models.extracted_field import ExtractionSource


class ConfidenceService:
    """
    Calculates confidence scores based on how a field was extracted.
    Scores reflect the reliability of the extraction method rather than
    arbitrary hardcoded values.
    """

    SCORES = {
        ExtractionSource.REGEX_WITH_LABEL: 0.95,
        ExtractionSource.REGEX_WITHOUT_LABEL: 0.75,
        ExtractionSource.FALLBACK: 0.50,
        ExtractionSource.NOT_FOUND: 0.0,
    }

    def score(self, source: ExtractionSource) -> float:
        return self.SCORES.get(source, 0.0)

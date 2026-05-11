import nltk
from app.applications.use_cases.extractors.base_extractor import BaseExtractor
from app.applications.use_cases.confidence_service import ConfidenceService
from app.domain.models.extracted_field import ExtractedField, ExtractionSource
from app.domain.models.extraction_result import ExtractionResult


class NLPExtractor(BaseExtractor):

    def __init__(self):
        self._confidence = ConfidenceService()
        nltk.download("punkt_tab", quiet=True)
        nltk.download("averaged_perceptron_tagger_eng", quiet=True)
        nltk.download("maxent_ne_chunker_tab", quiet=True)
        nltk.download("words", quiet=True)

    def extract(self, text: str) -> ExtractionResult:
        entities = self._get_entities(text)
        fields = {
            "vendor_name": self._field_from_entities(entities["ORGANIZATION"]),
            "vendor_address": self._field_from_entities(entities["GPE"]),
            "bill_to": self._field_from_entities(entities["PERSON"]),
            "invoice_number": self._field_from_entities([]),
            "date": self._field_from_entities([]),
        }
        return ExtractionResult(fields=fields, line_items=[])

    def _get_entities(self, text: str) -> dict:
        tokens = nltk.word_tokenize(text)
        tagged = nltk.pos_tag(tokens)
        tree = nltk.ne_chunk(tagged)

        entities = {"ORGANIZATION": [], "PERSON": [], "GPE": []}
        for subtree in tree:
            if hasattr(subtree, "label") and subtree.label() in entities:
                entity_text = " ".join(word for word, tag in subtree.leaves())
                entities[subtree.label()].append(entity_text)
        return entities

    def _field_from_entities(self, entities_list: list) -> ExtractedField:
        source = (
            ExtractionSource.FALLBACK if entities_list else ExtractionSource.NOT_FOUND
        )
        return ExtractedField(
            value=entities_list[0] if entities_list else "NOT_FOUND",
            confidence=self._confidence.score(source),
            source=source,
        )

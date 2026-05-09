from abc import ABC, abstractmethod
from app.domain.models.extraction_result import ExtractionResult


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, text: str) -> ExtractionResult:
        pass

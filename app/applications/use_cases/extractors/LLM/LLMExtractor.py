from app.applications.use_cases.extractors.base_extractor import BaseExtractor
from groq import Groq
from app.domain.models.extraction_result import ExtractionResult
from app.applications.use_cases.confidence_service import ConfidenceService
from app.domain.models.extracted_field import ExtractedField, ExtractionSource
import os
import re
import json


class LLMExtractor(BaseExtractor):

    def __init__(self):
        self._client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self._confidence = ConfidenceService()

    def extract(self, text: str) -> ExtractionResult:
        completion = self._client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": self._build_prompt(text)}],
            temperature=0,
            max_completion_tokens=1024,
        )
        response = completion.choices[0].message.content
        match = re.search(r"\{.*\}", response, re.DOTALL)
        data = json.loads(match.group()) if match else {}
        fields = {}
        for key in [
            "vendor_name",
            "vendor_address",
            "bill_to",
            "invoice_number",
            "date",
        ]:
            value = data.get(key, "NOT_FOUND")
            source = (
                ExtractionSource.FALLBACK
                if value != "NOT_FOUND"
                else ExtractionSource.NOT_FOUND
            )
            fields[key] = ExtractedField(
                value=value,
                confidence=self._confidence.score(source),
                source=source,
            )
        return ExtractionResult(fields=fields, line_items=[])

    def _build_prompt(self, text: str) -> str:
        return f"""You are an invoice data extractor. Extract the following fields from the invoice text below and return ONLY a valid JSON object with these exact keys:
                - vendor_name: company or person name of the vendor/seller only, no address
                - vendor_address: full address of the vendor/seller
                - bill_to: company or person name of the customer/buyer only, no address
                - invoice_number: the invoice number or ID
                - date: the invoice issue date

                If a field is not found, use "NOT_FOUND" as the value.
                Return ONLY the JSON object, no explanation, no markdown.

                Invoice text:
                {text}"""

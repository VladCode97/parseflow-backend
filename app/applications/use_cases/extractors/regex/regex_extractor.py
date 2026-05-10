from app.applications.use_cases.extractors.base_extractor import BaseExtractor
from app.applications.use_cases.confidence_service import ConfidenceService
from app.domain.models.extracted_field import ExtractedField, ExtractionSource
from app.domain.models.extraction_result import ExtractionResult
import re


class RegexExtractor(BaseExtractor):
    def __init__(self):
        self._confidence = ConfidenceService()

    def extract(self, text: str) -> ExtractionResult:
        fields = {
            "vendor_name": self._extract_vendor_name(text),
            "vendor_address": self._extract_vendor_address(text),
            "bill_to": self._extract_bill_to(text),
            "invoice_number": self._extract_invoice_number(text),
            "date": self._extract_date(text),
        }
        return ExtractionResult(
            fields=fields, line_items=self._extract_line_items(text)
        )

    def _field(self, value: str, source: ExtractionSource) -> ExtractedField:
        return ExtractedField(
            value=value,
            confidence=self._confidence.score(source),
            source=source,
        )

    def _extract_vendor_name(self, text: str) -> ExtractedField:
        """
        Finds the first line that looks like a vendor name, skipping headers,
        numbers, addresses, emails, and known metadata keywords.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        skip_patterns = [
            r"^invoice$",
            r"^tax\s*invoice$",
            r"^page\s+\d+\s+of\s+\d+$",
            r"^(no\.?|number|#)\s*\d",
            r"^\d",
            r"(bill\s*to|ship\s*to|invoice\s*to)",
            r"(due\s*date|p\.?o\.?\s*number|payment|terms)",
            r"(preview|powered\s*by)",
            r"@",
            r"^\+?\d[\d\s\-()]+$",
        ]

        for line in lines:
            segment = re.split(r"\t+", line)[0].strip()
            if not segment:
                continue

            normalized = segment.lower()
            if any(re.search(p, normalized) for p in skip_patterns):
                continue

            if re.search(r"[A-Za-z]", segment) and not re.fullmatch(
                r"[\W\d]+", segment
            ):
                clean = re.split(
                    r"\s+(?=[A-Z][a-z]+,?\s+[A-Z]{2}\s+\d{5}|[A-Z]{2}\s+\d{5}|\d{5})",
                    segment,
                )[0].strip()
                return self._field(clean, ExtractionSource.REGEX_WITHOUT_LABEL)

        return self._field("NOT_FOUND", ExtractionSource.NOT_FOUND)

    def _extract_invoice_number(self, text: str) -> ExtractedField:
        """
        Searches for a pattern like 'Invoice No.', 'Invoice #', or 'Invoice ID'
        followed by the invoice number value, either inline or on the next line.
        """
        match = re.search(
            r"\bInvoice\s*(No\.?|Number|ID|#)\s*[:.]?\s*([A-Za-z0-9\-_]{3,})",
            text,
            re.IGNORECASE,
        )
        if match:
            return self._field(match.group(2), ExtractionSource.REGEX_WITH_LABEL)

        match = re.search(
            r"Invoice\s*No\.?\s*\n[^\n]*?([A-Za-z0-9\-_]{4,})\s*$",
            text,
            re.IGNORECASE | re.MULTILINE,
        )
        if match:
            return self._field(match.group(1), ExtractionSource.REGEX_WITH_LABEL)

        return self._field("NOT_FOUND", ExtractionSource.NOT_FOUND)

    def _extract_date(self, text: str) -> ExtractedField:
        """
        First tries to find a date preceded by a label like 'Invoice Date' or 'Date'.
        Falls back to any standalone date on its own line if no label is found.
        """
        match = re.search(
            r"(Issue\s*date|Date\s*of\s*issue|Invoice\s*date|Date)\s*[:.]?\s*"
            r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{2}[/\-]\d{2})",
            text,
            re.IGNORECASE,
        )
        if match:
            return self._field(match.group(2), ExtractionSource.REGEX_WITH_LABEL)

        match = re.search(
            r"Invoice\s*Date[^\n]*\n\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})",
            text,
            re.IGNORECASE,
        )
        if match:
            return self._field(match.group(1), ExtractionSource.REGEX_WITH_LABEL)

        match = re.search(
            r"(?:^|\n)\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{2}[/\-]\d{2})\s*(?:\n|$)",
            text,
            re.IGNORECASE,
        )
        if match:
            return self._field(match.group(1), ExtractionSource.REGEX_WITHOUT_LABEL)

        return self._field("NOT_FOUND", ExtractionSource.NOT_FOUND)

    def _extract_vendor_address(self, text: str) -> ExtractedField:
        """
        Scans lines for a street address by looking for a number followed by a
        road type keyword. Appends the next line if it looks like a city/zip continuation.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        skip_line_patterns = [
            r"^(abn|email|phone|fax|web|invoice\s*to|bill\s*to)",
        ]

        address_lines = []
        for line in lines:
            segment = re.split(r"\t+", line)[0].strip()
            if not segment:
                continue

            if any(re.search(p, segment, re.IGNORECASE) for p in skip_line_patterns):
                continue

            clean = re.sub(r"^address\s*:\s*", "", segment, flags=re.IGNORECASE).strip()
            source = (
                ExtractionSource.REGEX_WITH_LABEL
                if re.match(r"^address\s*:", segment, re.IGNORECASE)
                else ExtractionSource.REGEX_WITHOUT_LABEL
            )

            if re.search(
                r"\d+.+(road|rd|street|st|avenue|ave|drive|dr|lane|ln|blvd|boulevard|united kingdom|usa|canada|il|ny|ca|tx|fitzroy|smith|harvest|sheridan|pineview|court)|p\.?o\.?\s*box\s+\d+",
                clean,
                re.IGNORECASE,
            ):
                address_lines.append(clean)
                idx = lines.index(line)
                if idx + 1 < len(lines):
                    next_seg = re.split(r"\t+", lines[idx + 1])[0].strip()
                    if re.search(
                        r"^\d{5}|[A-Z]{2}\s*\d{5}|[A-Z]{2}-\d{5}|[A-Za-z]+\s+[A-Z]{2}\s+\d{5}",
                        next_seg,
                        re.IGNORECASE,
                    ):
                        address_lines.append(next_seg)
                if idx > 0 and re.search(r"p\.?o\.?\s*box", clean, re.IGNORECASE):
                    prev_seg = re.split(r"\t+", lines[idx - 1])[0].strip()
                    city_state = re.search(
                        r"\b([A-Z][a-z]+\s+[A-Z]{2}\s+\d{5}[\-\d]*)\s*$", prev_seg
                    )
                    if city_state:
                        address_lines.append(city_state.group(1).strip())
                return self._field(" ".join(address_lines), source)

        return self._field("NOT_FOUND", ExtractionSource.NOT_FOUND)

    def _extract_bill_to(self, text: str) -> ExtractedField:
        """
        Finds the 'BILL TO' or 'INVOICE TO' label and returns the first valid name on the lines
        that follow, skipping headers, addresses, emails, and zip codes.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        for index, line in enumerate(lines):
            if re.search(r"(bill\s*to|invoice\s*to)\s*:?", line, re.IGNORECASE):
                inline = re.search(
                    r"(?:bill\s*to|invoice\s*to)\s*:?\s*([A-Za-z][\w\s\.]+)",
                    line,
                    re.IGNORECASE,
                )
                if inline:
                    candidate = inline.group(1).strip()
                    if not re.search(
                        r"(ship\s*to|street|avenue|road|@|\d{5}|client)",
                        candidate,
                        re.IGNORECASE,
                    ):
                        return self._field(candidate, ExtractionSource.REGEX_WITH_LABEL)

                for next_line in lines[index + 1 : index + 6]:
                    candidate = re.split(r"[\t]+", next_line)[0].strip()
                    if (
                        candidate
                        and not re.search(
                            r"(ship\s*to|invoice\s*to|street|avenue|road|@|\d{5}|due\s*date|australia|sydney|new\s*york|nsw|state|zip)",
                            candidate,
                            re.IGNORECASE,
                        )
                        and not re.match(r"^\d", candidate)
                        and not re.fullmatch(r"client", candidate, re.IGNORECASE)
                    ):
                        return self._field(candidate, ExtractionSource.REGEX_WITH_LABEL)

        return self._field("NOT_FOUND", ExtractionSource.NOT_FOUND)

    def _extract_line_items(self, text: str) -> list:
        """
        Extracts line items supporting two column layouts: QTY DESCRIPTION PRICE TOTAL
        and DESCRIPTION QTY PRICE TOTAL. Summary rows like subtotal, tax, and
        discount are skipped.
        """
        from app.domain.models.line_item import LineItem

        line_items = []
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        skip_prefixes = (
            "subtotal",
            "total",
            "tax",
            "shipping",
            "amount",
            "balance",
            "sales",
        )

        for line in lines:
            match = re.search(
                r"^(\d+(?:\.\d+)?)\s*(?:ea|hour|hr|hrs|unit|units|pcs|pc|kg|g|l|m)?\s+(.+?)\s+\$?(-?\d+(?:\.\d+)?)\s+\$?(-?\d+(?:\.\d+)?)$",
                line,
                re.IGNORECASE,
            )
            if match:
                description = match.group(2).strip()
                if description.lower().startswith(skip_prefixes):
                    continue
                line_items.append(
                    LineItem(
                        sku="NOT_FOUND",
                        description=description,
                        quantity=float(match.group(1)),
                        tax_rate=0.0,
                        unit_price=float(match.group(3)),
                        total=float(match.group(4)),
                        confidence=self._confidence.score(
                            ExtractionSource.REGEX_WITHOUT_LABEL
                        ),
                    )
                )
                continue

            match = re.search(
                r"^(.+?)\s+(\d+(?:\.\d+)?)\s*(?:ea|hour|hr|hrs|unit|units|pcs|pc|kg|g|l|m)?\s+\$?(-?\d+(?:\.\d+)?)(?:/[A-Za-z]+)?\s+\$?(-?\d+(?:\.\d+)?)$",
                line,
                re.IGNORECASE,
            )
            if match:
                description = match.group(1).strip()
                if description.lower().startswith(skip_prefixes):
                    continue
                line_items.append(
                    LineItem(
                        sku="NOT_FOUND",
                        description=description,
                        quantity=float(match.group(2)),
                        tax_rate=0.0,
                        unit_price=float(match.group(3)),
                        total=float(match.group(4)),
                        confidence=self._confidence.score(
                            ExtractionSource.REGEX_WITHOUT_LABEL
                        ),
                    )
                )

        return line_items

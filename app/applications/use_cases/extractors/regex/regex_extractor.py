from app.applications.use_cases.extractors.base_extractor import BaseExtractor
from app.domain.models.extracted_field import ExtractedField
from app.domain.models.extraction_result import ExtractionResult
import re


class RegexExtractor(BaseExtractor):
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

    def _extract_vendor_name(self, text: str) -> ExtractedField:
        """
        Finds the first line that looks like a vendor name, skipping headers,
        numbers, addresses, emails, and known metadata keywords.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        skip_patterns = [
            r"^invoice$",
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
                return ExtractedField(value=segment, confidence=0.85)

        return ExtractedField(value="NOT_FOUND", confidence=0.0)

    def _extract_invoice_number(self, text: str) -> ExtractedField:
        """
        Searches for a pattern like 'Invoice No.', 'Invoice #', or 'Invoice ID'
        followed by the invoice number value.
        """
        match = re.search(
            r"\bInvoice\s*(No\.?|Number|ID|#)\s*[:.]?\s*([A-Za-z0-9\-_]+)",
            text,
            re.IGNORECASE,
        )
        if not match:
            return ExtractedField(value="NOT_FOUND", confidence=0.0)
        return ExtractedField(value=match.group(2), confidence=0.95)

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
            return ExtractedField(value=match.group(2), confidence=0.90)

        match = re.search(
            r"(?:^|\n)\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[/\-]\d{2}[/\-]\d{2})\s*(?:\n|$)",
            text,
            re.IGNORECASE,
        )
        if match:
            return ExtractedField(value=match.group(1), confidence=0.75)

        return ExtractedField(value="NOT_FOUND", confidence=0.0)

    def _extract_vendor_address(self, text: str) -> ExtractedField:
        """
        Scans lines for a street address by looking for a number followed by a
        road type keyword. Appends the next line if it looks like a city/zip continuation.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        address_lines = []
        for line in lines:
            segment = re.split(r"\t+", line)[0].strip()
            if not segment:
                continue

            if re.search(
                r"\d+.+(road|rd|street|st|avenue|ave|drive|dr|lane|ln|blvd|boulevard|united kingdom|usa|canada|il|ny|ca|tx)",
                segment,
                re.IGNORECASE,
            ):
                address_lines.append(segment)
                idx = lines.index(line)
                if idx + 1 < len(lines):
                    next_seg = re.split(r"\t+", lines[idx + 1])[0].strip()
                    if re.search(r"^\d{5}|[A-Z]{2}\s*\d{5}|[A-Z]{2}-\d{5}", next_seg):
                        address_lines.append(next_seg)
                break

        if address_lines:
            return ExtractedField(value=" ".join(address_lines), confidence=0.80)

        return ExtractedField(value="NOT_FOUND", confidence=0.0)

    def _extract_bill_to(self, text: str) -> ExtractedField:
        """
        Finds the 'BILL TO' label and returns the first valid name on the lines
        that follow, skipping headers, addresses, emails, and zip codes.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        for index, line in enumerate(lines):
            if re.search(r"bill\s*to\s*:?", line, re.IGNORECASE):
                for next_line in lines[index + 1 : index + 6]:
                    candidate = re.split(r"[\t]+", next_line)[0].strip()
                    if candidate and not re.search(
                        r"(ship\s*to|invoice\s*to|street|avenue|road|@|\d{5}|client)",
                        candidate,
                        re.IGNORECASE,
                    ):
                        return ExtractedField(value=candidate, confidence=0.90)

        return ExtractedField(value="NOT_FOUND", confidence=0.0)

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
            "discount",
            "shipping",
            "amount",
            "balance",
            "sales",
        )

        for line in lines:
            match = re.search(
                r"^(\d+(?:\.\d+)?)\s+(.+?)\s+\$?(\d+(?:\.\d+)?)\s+\$?(\d+(?:\.\d+)?)$",
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
                        confidence=0.85,
                    )
                )
                continue

            match = re.search(
                r"^(.+?)\s+(\d+(?:\.\d+)?)\s+\$?(\d+(?:\.\d+)?)(?:/[A-Za-z]+)?\s+\$?(\d+(?:\.\d+)?)$",
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
                        confidence=0.85,
                    )
                )

        return line_items

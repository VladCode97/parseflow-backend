from app.applications.use_cases.extractors.regex.regex_extractor import RegexExtractor


extractor = RegexExtractor()


# INVOICE TESTS


def test_extract_invoice_number():
    text = "Invoice No: US-0001"
    result = extractor.extract(text)
    assert result.fields["invoice_number"].value == "US-0001"


def test_extract_invoice_number_not_found():
    text = "INVOICE\nJohn Smith\nNew York"
    result = extractor.extract(text)
    assert result.fields["invoice_number"].value == "NOT_FOUND"


# DATE TESTS


def test_extract_date_label():
    text = "Invoice Date: 11/02/2019"
    result = extractor.extract(text)
    assert result.fields["date"].value == "11/02/2019"


def test_extract_date_without_label():
    text = "INVOICE\n11/02/2019\nJohn Smith"
    result = extractor.extract(text)
    assert result.fields["date"].value == "11/02/2019"


def test_extract_date_not_found():
    text = "INVOICE\nJohn Smith\nNew York"
    result = extractor.extract(text)
    assert result.fields["date"].value == "NOT_FOUND"


# VENDOR NAME TESTS


def test_extract_vendor_name():
    text = "East Repair Inc.\n1912 Harvest Lane\nNew York NY 12210"
    result = extractor.extract(text)
    assert result.fields["vendor_name"].value == "East Repair Inc."


def test_extract_vendor_name_skips():
    text = "INVOICE\nEast Repair Inc.\n1912 Harvest Lane"
    result = extractor.extract(text)
    assert result.fields["vendor_name"].value == "East Repair Inc."


# BILL TO TESTS


def test_extract_bill_to_with_label():
    text = "INVOICE\nBILL TO:\nJohn Smith\n123 Main Street"
    result = extractor.extract(text)
    assert result.fields["bill_to"].value == "John Smith"


def test_extract_bill_to_invoice_to_inline():
    text = "INVOICE\nInvoice to: Company Pty Ltd\nInvoice ID: 001"
    result = extractor.extract(text)
    assert result.fields["bill_to"].value == "Company Pty Ltd"


def test_extract_bill_to_not_found():
    text = "INVOICE\nEast Repair Inc.\n1912 Harvest Lane"
    result = extractor.extract(text)
    assert result.fields["bill_to"].value == "NOT_FOUND"


# VENDOR ADDRESS TESTS
def test_extract_vendor_address():
    text = "Your Company\n123 Main Street\nSydney NSW 2000"
    result = extractor.extract(text)
    assert result.fields["vendor_address"].value == "123 Main Street"


# LINE ITEMS TEST TESTS
def test_extract_line_items_qty_first():
    text = "INVOICE\nDESCRIPTION QTY PRICE TOTAL\n1 Front and rear brake cables 100.00 100.00"
    result = extractor.extract(text)
    assert len(result.line_items) == 1
    assert result.line_items[0].description == "Front and rear brake cables"
    assert result.line_items[0].quantity == 1.0


def test_extract_line_items_description_first():
    text = "INVOICE\nItem 1 2 100.00 200.00"
    result = extractor.extract(text)
    assert len(result.line_items) == 1
    assert result.line_items[0].quantity == 2.0
    assert result.line_items[0].total == 200.0

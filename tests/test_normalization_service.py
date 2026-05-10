from app.applications.use_cases.normalization_service import NormalizationService

service = NormalizationService()


def test_removes_extra_spaces():
    text = "INVOICE\t\t\tJohn Smith"
    result = service.normalize(text)
    assert "\t" not in result


def test_normalizes_line_breaks():
    text = "INVOICE\n\n\nJohn Smith"
    result = service.normalize(text)
    assert "\n\n" not in result

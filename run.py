import argparse
import base64
import json
import os
import sys

from dotenv import load_dotenv
from app.applications.services.process_document import ProcessDocument
from app.infrastructure.ocr.veryfi_provider import VeryfiProvider


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        print(f"Error: missing required environment variable: {name}")
        sys.exit(1)
    return value


def build_provider() -> VeryfiProvider:
    return VeryfiProvider(
        api_key=get_required_env("VERYFI_API_KEY"),
        username=get_required_env("VERYFI_USERNAME"),
        client_id=get_required_env("VERYFI_CLIENT_ID"),
        client_secret=get_required_env("VERYFI_CLIENT_SECRET"),
    )


def process_url(url: str) -> dict:
    provider = build_provider()
    veryfi_response = provider.process(file=url)
    return ProcessDocument().process(ocr_text=veryfi_response["ocr_text"])


def process_file(filepath: str) -> dict:
    if not os.path.exists(filepath):
        print(f"Error: file not found: {filepath}")
        sys.exit(1)

    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        file_bytes = f.read()

    provider = build_provider()
    veryfi_response = provider.process(file=file_bytes, filename=filename)
    return ProcessDocument().process(ocr_text=veryfi_response["ocr_text"])


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="ParseFlow — extract structured data from invoices using Veryfi OCR"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--file", metavar="PATH", help="path to a local invoice file (PDF, JPG, PNG)"
    )
    group.add_argument("--url", metavar="URL", help="public URL of an invoice document")

    args = parser.parse_args()

    try:
        if args.url:
            result = process_url(args.url)
        else:
            result = process_file(args.file)

        print(json.dumps(result.model_dump(), indent=2))

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

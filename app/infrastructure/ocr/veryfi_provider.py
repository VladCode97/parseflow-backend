from __future__ import annotations
from pathlib import Path
from typing import Optional
from veryfi import Client
import tempfile


class VeryfiProvider:
    """
    Veryfi OCR Provider
    """
    def __init__(
        self, api_key: str, username: str, client_id: str, client_secret: str
    ) -> None:
        self._client = Client(
            api_key=api_key,
            username=username,
            client_id=client_id,
            client_secret=client_secret,
        )



    def _process_document_from_url(self, url: str):
        """
        Process document from url
        :param url: url of the document
        """
        return self._client.process_document_url(
            file_url=url,
            boost_mode=True,
            external_id="parseflow-ref",
            max_pages_to_process=5,
        )


    def _process_document_from_bytes(self, file: bytes, filename: str):
        """
        Process document from bytes
        :param file: bytes of the document
        :param filename: filename of the document
        :param content_type: content type of the document
        """
        extension = Path(filename).suffix
        with tempfile.NamedTemporaryFile(
            delete=True,
            suffix=extension,
        ) as temp_file:
            temp_file.write(file)
            temp_file.flush()
            return self._client.process_document(
                file_path=temp_file.name,
                boost_mode=True,
            )


    def process(self, file: str | bytes, filename: Optional[str] = None) -> dict:
        """
        generic processing entrypoint
        :param file: file of the document
        """
        if isinstance(file, str):
            return self._process_document_from_url(file)
        if isinstance(file, bytes):
            if filename is None:
                raise ValueError("Filename is required when processing from bytes")
            return self._process_document_from_bytes(file, filename)
        raise ValueError("Unsupported document type")

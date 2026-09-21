import asyncio
import base64
import io
import json
import re
from typing import Any

import aiohttp
from fastapi import UploadFile
from pydantic import BaseModel, Field
from starlette.datastructures import Headers

from open_webui.models.chats import Chats
from open_webui.models.users import UserModel
from open_webui.routers.files import upload_file_handler
from open_webui.utils.chat_id import is_saved_chat_id


class Tools:
    """Restricted proxy for the isolated I3S File Generator service."""

    _BASE_URL = "http://172.21.0.2:8081"
    _OPERATIONS = {
        "create_docx", "create_xlsx", "create_pptx", "create_pdf", "create_csv", "create_text_file", "create_chart",
        "convert_document", "inspect_document", "analyze_csv", "analyze_xlsx", "inspect_image", "ocr_image",
        "convert_image", "resize_image", "inspect_audio", "transcribe_audio", "inspect_video", "extract_keyframes",
        "transcribe_video", "analyze_video", "list_archive", "extract_archive", "create_archive",
    }
    _CELL = re.compile(r"^[A-Z]{1,3}[1-9][0-9]*$")

    class Valves(BaseModel):
        api_key: str = Field(default="", description="Private file-service key")

    def __init__(self):
        self.valves = self.Valves()

    @staticmethod
    def _filename(filename: str, extension: str) -> str:
        name = str(filename or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._ -]{0,120}", name):
            raise ValueError("filename contains unsupported characters")
        if not name.lower().endswith(extension):
            raise ValueError(f"filename must end in {extension}")
        return name

    @staticmethod
    def _rows(columns: list[str], rows: list[Any]) -> list[list[Any]]:
        if not columns:
            raise ValueError("at least one column is required")
        width = len(columns)
        if len(rows) > 5000:
            raise ValueError("too many rows")
        if not rows:
            return []
        if all(isinstance(row, dict) for row in rows):
            return [[row.get(column, "") for column in columns] for row in rows]
        if all(isinstance(row, (list, tuple)) for row in rows):
            normalized = [list(row) for row in rows]
        elif all(not isinstance(row, (list, tuple, dict)) for row in rows):
            if len(rows) % width:
                raise ValueError("flat rows must contain a complete value for every column")
            normalized = [list(rows[index:index + width]) for index in range(0, len(rows), width)]
        else:
            raise ValueError("rows must be row arrays, row objects, or a complete flat table")
        if any(len(row) > width for row in normalized):
            raise ValueError("a row has more values than columns")
        return [row + [""] * (width - len(row)) for row in normalized]

    def _formulas(self, formulas: dict[str, str]) -> dict[str, str]:
        if len(formulas) > 10000:
            raise ValueError("too many formulas")
        normalized = {}
        for cell, formula in formulas.items():
            cell = str(cell).upper()
            formula = str(formula).strip()
            if not self._CELL.fullmatch(cell):
                raise ValueError(f"invalid formula cell: {cell}")
            if not formula.startswith("=") or len(formula) > 512 or any(ch in formula for ch in "[]\r\n"):
                raise ValueError(f"invalid formula for {cell}")
            normalized[cell] = formula
        return normalized

    async def _attach_artifact(self, result: list, context: dict) -> list:
        """Store a service data URI as an Open WebUI-owned chat attachment."""
        if not context.get("request") or not context.get("user") or not isinstance(result, list) or len(result) != 2:
            return result
        info, data_uri = result
        if not isinstance(info, dict) or not isinstance(data_uri, str) or not data_uri.startswith("data:"):
            return result
        try:
            header, encoded = data_uri.split(",", 1)
            mime = header[5:].split(";", 1)[0]
            filename = self._filename(info.get("filename", ""), "." + str(info.get("filename", "")).rsplit(".", 1)[-1])
            if not mime or not header.endswith(";base64") or len(encoded) > 20 * 1024 * 1024:
                raise ValueError("invalid file-service artifact")
            data = base64.b64decode(encoded, validate=True)
            upload = UploadFile(filename=filename, file=io.BytesIO(data), headers=Headers({"content-type": mime}))
            uploaded = await upload_file_handler(
                context["request"], file=upload, metadata={"source": "i3s_file_generator"},
                process=False, process_in_background=False, user=UserModel(**context["user"]),
            )
            file_entry = {
                "type": "file", "id": uploaded.id, "url": str(context["request"].app.url_path_for("get_file_content_by_id", id=uploaded.id)),
                "name": uploaded.filename, "filename": uploaded.filename, "mime_type": mime, "content_type": mime,
                "size": len(data),
            }
            files = [file_entry]
            chat_id, message_id = context.get("chat_id"), context.get("message_id")
            if is_saved_chat_id(chat_id) and message_id:
                stored = await Chats.add_message_files_by_id_and_message_id(chat_id, message_id, files)
                if stored is not None:
                    files = stored
            if context.get("event_emitter"):
                await context["event_emitter"]({"type": "chat:message:files", "data": {"files": files}})
            return [{"status": "success", "filename": uploaded.filename, "file_id": uploaded.id, "message": "The generated file is attached to this conversation."}]
        except Exception as error:
            return [{"error": f"Open WebUI attachment failed: {error}"}]

    async def _call(self, operation: str, payload: dict, context: dict | None = None) -> list:
        if operation not in self._OPERATIONS:
            return [{"error": "invalid file operation"}]
        try:
            timeout = aiohttp.ClientTimeout(total=45)
            headers = {"Authorization": f"Bearer {self.valves.api_key}"}
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self._BASE_URL}/{operation}", json=payload, headers=headers) as response:
                    if response.content_length and response.content_length > 20 * 1024 * 1024:
                        return [{"error": "file-service response is too large"}]
                    raw_body = await response.text()
                    try:
                        body = json.loads(raw_body)
                    except json.JSONDecodeError:
                        body = {"message": raw_body[:500] or f"HTTP {response.status}"}
                    if response.status == 200:
                        return await self._attach_artifact(body, context or {})
                    return [{"error": "file-service validation failed", "status": response.status, "detail": body}]
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return [{"error": "file service unavailable"}]
        except ValueError as error:
            return [{"error": str(error)}]

    async def create_xlsx(self, filename: str, sheet_name: str, columns: list[str], rows: list[list[Any]], formulas: dict[str, str] = {}, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Create XLSX. Use row arrays matching columns and formulas such as {"D2":"=B2-C2"}."""
        try:
            name = self._filename(filename, ".xlsx")
            sheet = str(sheet_name or "Sheet1").strip()
            if not sheet or len(sheet) > 31 or any(char in sheet for char in "[]:*?\\/"):
                raise ValueError("invalid sheet_name")
            headers = [str(column) for column in columns]
            return await self._call("create_xlsx", {"filename": name, "sheets": [{"name": sheet, "columns": headers, "rows": self._rows(headers, rows), "formulas": self._formulas(formulas)}]}, {"request": __request__, "user": __user__, "event_emitter": __event_emitter__, "chat_id": __chat_id__, "message_id": __message_id__})
        except ValueError as error:
            return [{"error": str(error)}]

    async def create_docx(self, filename: str, title: str = "", paragraphs: list[str] = [], table_rows: list[list[str]] = [], __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Create a DOCX. table_rows is one optional rectangular table: [["A1","B1"],["A2","B2"]]."""
        try:
            if table_rows and (not all(isinstance(row, list) for row in table_rows) or not table_rows[0] or any(len(row) != len(table_rows[0]) for row in table_rows)):
                raise ValueError("table_rows must be a non-empty rectangular row matrix")
            tables = [[ [str(cell) for cell in row] for row in table_rows ]] if table_rows else []
            return await self._call("create_docx", {"filename": self._filename(filename, ".docx"), "title": title, "paragraphs": paragraphs, "tables": tables}, {"request": __request__, "user": __user__, "event_emitter": __event_emitter__, "chat_id": __chat_id__, "message_id": __message_id__})
        except ValueError as error:
            return [{"error": str(error)}]

    async def create_pptx(self, filename: str, title: str = "", paragraphs: list[str] = [], __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Create a PPTX. Title plus each paragraph becomes a slide."""
        try:
            return await self._call("create_pptx", {"filename": self._filename(filename, ".pptx"), "title": title, "paragraphs": paragraphs}, {"request": __request__, "user": __user__, "event_emitter": __event_emitter__, "chat_id": __chat_id__, "message_id": __message_id__})
        except ValueError as error:
            return [{"error": str(error)}]

    async def create_pdf(self, filename: str, title: str = "", content: str = "", paragraphs: list[str] = [], __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Create a PDF. Put normal prose in content, or use paragraphs for separate blocks; do not retry more than once after an error."""
        try:
            normalized = ([str(content)] if str(content).strip() else []) + [str(item) for item in paragraphs]
            return await self._call("create_pdf", {"filename": self._filename(filename, ".pdf"), "title": title, "paragraphs": normalized}, {"request": __request__, "user": __user__, "event_emitter": __event_emitter__, "chat_id": __chat_id__, "message_id": __message_id__})
        except ValueError as error:
            return [{"error": str(error)}]

    async def create_csv(self, filename: str, columns: list[str], rows: list[list[Any]], __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Create a CSV. Use row arrays matching the columns."""
        try:
            headers = [str(column) for column in columns]
            return await self._call("create_csv", {"filename": self._filename(filename, ".csv"), "sheets": [{"columns": headers, "rows": self._rows(headers, rows)}]}, {"request": __request__, "user": __user__, "event_emitter": __event_emitter__, "chat_id": __chat_id__, "message_id": __message_id__})
        except ValueError as error:
            return [{"error": str(error)}]

    async def create_text_file(self, filename: str, content: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Create a TXT, Markdown, or HTML file."""
        try:
            name = str(filename or "").strip()
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._ -]{0,120}\.(txt|md|html)", name, re.IGNORECASE):
                raise ValueError("filename must end in .txt, .md, or .html")
            return await self._call("create_text_file", {"filename": name, "content": str(content)}, {"request": __request__, "user": __user__, "event_emitter": __event_emitter__, "chat_id": __chat_id__, "message_id": __message_id__})
        except ValueError as error:
            return [{"error": str(error)}]

    async def create_chart(self, filename: str, labels: list[str], values: list[float], title: str = "Chart", __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Create a PNG bar chart from labels and numeric values."""
        try:
            if len(labels) != len(values) or not labels:
                raise ValueError("labels and values must have the same non-zero length")
            return await self._call("create_chart", {"filename": self._filename(filename, ".png"), "labels": labels, "values": values, "title": title}, {"request": __request__, "user": __user__, "event_emitter": __event_emitter__, "chat_id": __chat_id__, "message_id": __message_id__})
        except ValueError as error:
            return [{"error": str(error)}]

    async def _process(self, operation: str, payload: dict, __request__, __user__, __event_emitter__, __chat_id__, __message_id__) -> list:
        return await self._call(operation, payload, {"request": __request__, "user": __user__, "event_emitter": __event_emitter__, "chat_id": __chat_id__, "message_id": __message_id__})

    async def inspect_document(self, filename: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Inspect a document already created in this Toolbox session."""; return await self._process("inspect_document", {"filename": filename}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def convert_document(self, filename: str, output_format: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Convert a Toolbox document to PDF, DOCX, XLSX, PPTX, TXT, or CSV."""; return await self._process("convert_document", {"filename": filename, "output_format": output_format}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def analyze_csv(self, filename: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Summarize a CSV already in the Toolbox volume."""; return await self._process("analyze_csv", {"filename": filename}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def analyze_xlsx(self, filename: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Summarize an XLSX already in the Toolbox volume."""; return await self._process("analyze_xlsx", {"filename": filename}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def inspect_image(self, filename: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Inspect image dimensions and format."""; return await self._process("inspect_image", {"filename": filename}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def ocr_image(self, filename: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Extract text from an image using local Tesseract."""; return await self._process("ocr_image", {"filename": filename}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def inspect_audio(self, filename: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Inspect local audio metadata with ffprobe."""; return await self._process("inspect_audio", {"filename": filename}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def transcribe_audio(self, filename: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Transcribe audio when an approved local Whisper model is installed."""; return await self._process("transcribe_audio", {"filename": filename}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def inspect_video(self, filename: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Inspect local video metadata with ffprobe."""; return await self._process("inspect_video", {"filename": filename}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def extract_keyframes(self, filename: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Extract a keyframe image from a local video."""; return await self._process("extract_keyframes", {"filename": filename}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def transcribe_video(self, filename: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Transcribe local video audio when a local Whisper model is installed."""; return await self._process("transcribe_video", {"filename": filename}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def analyze_video(self, filename: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Return local video metadata and approved-backend availability."""; return await self._process("analyze_video", {"filename": filename}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def list_archive(self, filename: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """List a local ZIP archive."""; return await self._process("list_archive", {"filename": filename}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def resize_image(self, filename: str, width: int, height: int, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Resize a local image and attach the result."""; return await self._process("resize_image", {"filename": filename, "width": width, "height": height}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def convert_image(self, filename: str, output_format: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Convert a local image and attach the result."""; return await self._process("convert_image", {"filename": filename, "output_format": output_format}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def extract_archive(self, filename: str, __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Safely extract a local ZIP archive."""; return await self._process("extract_archive", {"filename": filename}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)
    async def create_archive(self, filename: str, members: list[str], __request__: Any = None, __user__: dict = None, __event_emitter__: Any = None, __chat_id__: str = None, __message_id__: str = None) -> list:
        """Create a ZIP from named Toolbox files and attach it."""; return await self._process("create_archive", {"filename": filename, "members": members}, __request__, __user__, __event_emitter__, __chat_id__, __message_id__)

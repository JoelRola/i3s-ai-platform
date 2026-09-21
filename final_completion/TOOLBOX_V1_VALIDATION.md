# Toolbox V1 validation — 2026-09-21 UTC

## Executed against the live isolated service

Authenticated internal service acceptance returned HTTP 200 for DOCX (title, paragraphs, 3×3 table), XLSX (formula `=A2+B2`), Unicode/wrapped PDF, one-slide PPTX, CSV, PNG chart, and Markdown text. The service returns a data URI to the Open WebUI proxy; that proxy uses Open WebUI's official `upload_file_handler` and emits a chat attachment file ID.

The final browser/API acceptance remains **PARTIAL** because an authenticated i3s-work user/admin session was not available during this run. Do not claim the attachment UI test is complete until an operator creates each artifact through i3s-work and sees the Open WebUI-owned attachment/download in the chat.

## Safety checks

The deployed container runs as UID 10001, has read-only root, no published ports, no privileged mode, and drops all capabilities. A crafted ZIP member `../escape.txt` was rejected with HTTP 400. The deployed archive handling additionally rejects absolute/backslash/symlink members and limits expansion to 200 files/100 MiB.

## Capability matrix

| Capability | State |
|---|---|
| DOCX/XLSX/PDF/PPTX/CSV/chart/text | PASS at isolated service; Open WebUI browser attachment pending |
| Image inspect/resize/convert | IMPLEMENTED; authenticated user-path acceptance pending |
| Image OCR | IMPLEMENTED; representative user image acceptance pending |
| PDF text/OCR | PARTIAL — PDF page inspection is implemented; scanned-PDF OCR has not been exposed/accepted |
| ZIP create/list/extract | IMPLEMENTED; traversal regression PASS |
| Audio metadata | IMPLEMENTED; no approved sample/model test |
| Whisper transcription | RUNTIME READY / MODEL NOT STAGED / FUNCTION UNTESTED |
| Video metadata/keyframe | IMPLEMENTED; no approved sample test |
| Video transcription | contingent on staged Whisper model |
| Semantic visual understanding | NOT DEPLOYED |

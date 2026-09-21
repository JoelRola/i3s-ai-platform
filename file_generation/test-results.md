# Validation results — 2026-09-16

The following ran through the official Open Terminal `/execute` API as isolated user `validation-user`, not merely as host-side files. Each format was reopened/validated by its generating library where applicable.

| Artifact | Result | Size | Validation |
|---|---:|---:|---|
| `test_report.docx` | PASS | 36,801 B | Created with heading, two paragraphs, 3×3 table |
| `test_finance.xlsx` | PASS | 5,024 B | Reopened with openpyxl; `D2` is `=B2-C2` |
| `test_presentation.pptx` | PASS | 29,909 B | Reopened with python-pptx; 3 slides |
| `test_summary.pdf` | PASS | 979 B | PDF magic header verified |
| `test_data.csv` | PASS | 45 B | Created through stdlib CSV writer |
| `revenue_chart.png` | PASS | 22,632 B | Reopened with Pillow as PNG |

API execution: process `20260916-142219-97fea1`, exit code 0, total observed API latency about 5.3 seconds.

## Deliberately not claimed

No authenticated Open WebUI admin or user session was available to configure the terminal connection or create the `i3s-work` workspace model through the supported UI/API. Consequently, Open WebUI attachment/download exposure and the uploaded-file-to-generated-file UI workflow are **not yet tested**. The provided admin configuration document is the remaining supported configuration step; it must be completed with an authenticated admin session and then tested through a real user chat.

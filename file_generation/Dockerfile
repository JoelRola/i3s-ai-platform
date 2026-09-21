# Official Open Terminal image, extended only with the document libraries
# required by i3s-work.  No host files or Docker socket are included.
FROM ghcr.io/open-webui/open-terminal:latest

USER root
RUN python3 -m pip install --no-cache-dir \
    python-docx \
    openpyxl \
    python-pptx \
    fpdf2 \
    Pillow \
    matplotlib

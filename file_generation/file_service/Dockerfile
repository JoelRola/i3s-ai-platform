FROM python:3.12-slim
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ffmpeg libreoffice-core libreoffice-writer libreoffice-calc libreoffice-impress \
    poppler-utils tesseract-ocr file libmagic1 zip unzip p7zip-full \
    fonts-dejavu-core fonts-liberation libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 app \
    && pip install --no-cache-dir \
       fastapi uvicorn httpx python-docx openpyxl python-pptx fpdf2 pypdf \
       pandas numpy matplotlib Pillow opencv-python-headless python-magic pytesseract \
       faster-whisper scenedetect
WORKDIR /app
COPY app.py /app/app.py
USER 10001:10001
ENV HOME=/tmp MPLCONFIGDIR=/tmp/matplotlib XDG_CACHE_HOME=/data/cache
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8081"]

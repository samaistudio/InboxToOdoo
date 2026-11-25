FROM python:3.12-slim@sha256:a0e2dd78cc679ddfffea960fe45ecfcff9ac2f68d67917a0edfcde5c2100151b
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-deu tesseract-ocr-eng poppler-utils \
    && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir pypdf==5.1.0
COPY server.py /app/server.py
CMD ["python", "/app/server.py"]

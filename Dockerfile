FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install paddlepaddle first with numpy pinned
RUN pip install --no-cache-dir "numpy<2.0" paddlepaddle==3.3.0

# Then install rest of requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --no-deps paddleocr==2.7.3
RUN pip install --no-cache-dir -r requirements.txt

RUN PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True python -c "from paddleocr import PaddleOCR; PaddleOCR(lang='japan')"

COPY src/ ./src/

EXPOSE 8000
ENV PYTHONPATH=/app/src

CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
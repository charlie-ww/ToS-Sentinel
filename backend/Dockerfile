FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium

COPY . .

EXPOSE 8000

# 使用 Cloud Run 的 PORT 環境變數（默認 8000）
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
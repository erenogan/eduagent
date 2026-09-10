FROM python:3.12-slim

WORKDIR /app

# Önce requirements'ı kopyala ve kur (katman önbelleği için)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sonra kodu kopyala
COPY . .

# Render PORT'u ortam değişkeni olarak verir
EXPOSE 8000

# Production sunucusu (--reload YOK)
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
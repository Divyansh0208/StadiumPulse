FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/shared /app/backend/shared
COPY backend/navigator /app/backend/navigator
COPY data /app/data

ENV PYTHONPATH=/app
ENV VENUE_KB_PATH=/app/data/venue_kb.json

EXPOSE 8001

CMD ["uvicorn", "backend.navigator.app.main:app", "--host", "0.0.0.0", "--port", "8001"]

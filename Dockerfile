FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements-runtime.txt .
RUN python -m pip install --no-cache-dir -r requirements-runtime.txt

COPY src ./src
COPY scripts ./scripts
COPY sql ./sql

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "src/f1_strategy/dashboard.py", "--server.address=0.0.0.0", "--server.port=8501"]

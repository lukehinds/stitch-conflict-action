FROM python:3.11-slim

WORKDIR /app

COPY resolve_conflicts/ ./resolve_conflicts
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "resolve_conflicts/main.py"]

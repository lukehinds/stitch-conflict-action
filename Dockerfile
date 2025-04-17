FROM python:alpine

WORKDIR /app

COPY resolve_conflicts/ ./resolve_conflicts
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "stitch-conflict-action/main.py"]

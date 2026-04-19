FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY graph_db/ graph_db/

RUN pip install --no-cache-dir -e ".[api]"

EXPOSE 8000

CMD ["uvicorn", "graph_db.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

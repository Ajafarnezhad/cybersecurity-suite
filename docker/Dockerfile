# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/

RUN pip install --no-cache-dir -e .

ENV FLASK_APP=cybersecurity_suite.wsgi:app \
    LOG_DIR=/app/logs \
    REPORTS_DIR=/app/reports

RUN mkdir -p /app/logs /app/reports && chown -R app:app /app

USER app

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/')" || exit 1

CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "cybersecurity_suite.wsgi:app"]

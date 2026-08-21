FROM python:3.11.9-slim-bookworm@sha256:8fb099199b9f2d70342674bd9dbccd3ed03a258f26bbd1d556822c6dfc60c317

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HOME=/home/cineverity

COPY requirements-container.lock ./
RUN python -m pip install --no-cache-dir -r requirements-container.lock \
    && python -m pip check

RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin cineverity

COPY --chown=cineverity:cineverity src/ ./src/

USER cineverity

CMD ["sh", "-c", "exec python -m uvicorn src.backend.app:app --host 0.0.0.0 --port \"$PORT\" --workers 1"]
FROM python:3.11-slim
WORKDIR /service
COPY requirements.txt .
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN chmod -R a+rX /service/app && mkdir /data && chown 65534:65534 /data
USER 65534:65534
ENV DATABASE_URL=sqlite:////data/tickets.db
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

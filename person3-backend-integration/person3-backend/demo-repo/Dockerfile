# Build this trusted verifier image once. Never build an AI-generated Dockerfile.
FROM python:3.11-slim
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export PIP_CERT=/run/secrets/proxy_ca; fi; \
    pip install --no-cache-dir pytest==8.3.5
WORKDIR /workspace
USER 65534:65534
ENTRYPOINT ["python", "-m", "pytest"]
CMD ["-q", "-p", "no:cacheprovider"]

# Offline pytest-capable image for `witnis verify --profile container`.
# Build once (needs network); later runs stay `--network none`.
#
#   docker build -t witnis-verify:3.12 -f docker/verify.Dockerfile docker
#   set WITNIS_VERIFY_IMAGE=witnis-verify:3.12
FROM python:3.12-slim
RUN pip install --no-cache-dir pytest

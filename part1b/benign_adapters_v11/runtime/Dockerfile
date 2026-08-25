FROM ghcr.io/astral-sh/uv:python3.12-bookworm@sha256:9aa60c50016c0485636ab9a830246a6ef3399aa4a8bab3d17ef4a2358fba2ca7

LABEL org.opencontainers.image.source="https://github.com/apolmig/agencytransfer"
LABEL org.opencontainers.image.title="ERA Part 1B benign adapters v10 runtime"
LABEL org.opencontainers.image.version="v10"

ENV HF_HOME=/home/era/.cache/huggingface \
    PATH=/opt/era-venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_NO_PROGRESS=1

WORKDIR /opt/era-part1b
COPY requirements.lock ./requirements.lock
RUN uv venv --python python3.12 /opt/era-venv \
    && uv pip install \
        --python /opt/era-venv/bin/python \
        --no-cache \
        --requirement requirements.lock
RUN test -x /opt/era-venv/bin/python \
    && test -x /bin/sh \
    && command -v base64 >/dev/null \
    && command -v cut >/dev/null \
    && command -v gzip >/dev/null \
    && command -v sha256sum >/dev/null \
    && /opt/era-venv/bin/python --version

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin era
USER 10001:10001
ENTRYPOINT []
CMD ["/opt/era-venv/bin/python", "--version"]

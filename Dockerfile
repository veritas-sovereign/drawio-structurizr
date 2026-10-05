# syntax=docker/dockerfile:1.7
# drawio-structurizr with a pinned structurizr-cli, so --validate and --export work without Java on the host.

# Base image pinned by digest (multi-arch index); Dependabot proposes updates.
FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3

# structurizr-cli release and the SHA-256 of its structurizr-cli.zip asset
ARG STRUCTURIZR_CLI_VERSION=2025.11.09
ARG STRUCTURIZR_CLI_SHA256=f5365a463fc44d539ed19bec00c48ba1e1ecda0ccfd1ba40d2e7472d264eb79a

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

# Java runtime plus structurizr-cli; curl and unzip are removed in the same layer
RUN apt-get update \
 && apt-get install -y --no-install-recommends default-jre-headless ca-certificates curl unzip \
 && curl -fsSL -o /tmp/structurizr-cli.zip \
      "https://github.com/structurizr/cli/releases/download/v${STRUCTURIZR_CLI_VERSION}/structurizr-cli.zip" \
 && echo "${STRUCTURIZR_CLI_SHA256}  /tmp/structurizr-cli.zip" | sha256sum -c - \
 && mkdir -p /opt/structurizr-cli \
 && unzip -q /tmp/structurizr-cli.zip -d /opt/structurizr-cli \
 && rm /tmp/structurizr-cli.zip \
 && chmod +x /opt/structurizr-cli/structurizr.sh \
 && ln -s /opt/structurizr-cli/structurizr.sh /usr/local/bin/structurizr-cli \
 && apt-get purge -y curl unzip \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
RUN pip install . && rm -rf /src

RUN useradd --create-home --uid 10001 app
USER app

WORKDIR /work
ENTRYPOINT ["drawio-structurizr"]
CMD ["--help"]

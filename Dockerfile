# syntax=docker/dockerfile:1.7

ARG PYTHON_IMAGE=python:3.11.9-slim-bookworm@sha256:8fb099199b9f2d70342674bd9dbccd3ed03a258f26bbd1d556822c6dfc60c317

FROM ${PYTHON_IMAGE} AS wheels

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       ca-certificates \
       git \
       sleuthkit \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY pyproject.toml README.md LICENSE MANIFEST.in DECISIONS.md compose.yaml ./
COPY src ./src
COPY tests ./tests

# The sift-sentinel dependency is Git-SHA pinned. Resolve it only in this
# networked builder; the final image installs exclusively from this wheelhouse.
RUN python -m pip wheel --wheel-dir /wheels . \
    && mkdir /sentinel-wheel \
    && mv /wheels/sentinel_unchained-*.whl /sentinel-wheel/


FROM wheels AS test

# The release tests intentionally inspect the freeze/controller documentation,
# setup entrypoint, Docker policy, and pinned requirements. They are copied only
# into this disposable test stage; the final runtime still receives wheels only.
COPY .gitattributes .dockerignore Dockerfile setup.ps1 get.ps1 get.sh ./
COPY docs ./docs
COPY requirements ./requirements
COPY scripts ./scripts

RUN git init \
    && git config user.name "Unchained Docker Gate" \
    && git config user.email "docker-gate@example.invalid" \
    && git add --all \
    && git commit -m "Docker test context" \
    && python -m pip install --no-index --find-links=/wheels /wheels/*.whl \
    && python -m pip install --no-index --no-deps /sentinel-wheel/*.whl \
    && python -m pip install \
       build==1.5.1 \
       markdown-it-py==4.0.0 \
       pytest==9.0.2 \
       ruff==0.15.6 \
    && python -m pip check \
    && python -m pytest -q \
    && python -m ruff check . \
    && python -m ruff format --check . \
    && python -m unchained onboard --json >/dev/null \
    && python -m build


FROM ${PYTHON_IMAGE} AS runtime

ARG VCS_REF=unknown
ARG BUILD_DATE=unknown

LABEL org.opencontainers.image.title="Unchained" \
      org.opencontainers.image.description="Bounded GPT-5.6 Digital Forensics & Incident Response (DFIR) investigator with offline-verifiable proof" \
      org.opencontainers.image.source="https://github.com/3sk1nt4n/Unchained" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.licenses="MIT"

ENV PATH=/opt/sentinel/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    SENTINEL_IMAGE_REVISION=${VCS_REF}

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       ca-certificates \
       sleuthkit \
       tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 sentinel \
    && useradd --uid 10001 --gid 10001 \
       --create-home --home-dir /home/sentinel sentinel \
    && python -m venv /opt/sentinel

COPY --from=wheels /wheels /wheels
COPY --from=wheels /sentinel-wheel /sentinel-wheel

# Install every pre-resolved production wheel together. This satisfies the
# commit-pinned direct dependency without placing Git in the runtime image.
RUN /opt/sentinel/bin/python -m pip install \
       --no-index --find-links=/wheels /wheels/*.whl \
    && /opt/sentinel/bin/python -m pip install \
       --no-index --no-deps /sentinel-wheel/*.whl \
    && /opt/sentinel/bin/python -m pip check \
    && /opt/sentinel/bin/sentinel onboard --json >/dev/null \
    && rm -rf /wheels /sentinel-wheel \
    && mkdir -p /workspace/unchained-runs /home/sentinel/.cache \
    && chown -R sentinel:sentinel /workspace /home/sentinel

WORKDIR /workspace
USER 10001:10001

ENTRYPOINT ["/usr/bin/tini", "--", "sentinel"]
CMD ["--help"]

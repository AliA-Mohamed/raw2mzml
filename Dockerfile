FROM debian:bookworm-slim

LABEL maintainer="AliA-Mohamed"
LABEL description="Convert Thermo .raw files to polarity-split .mzML"
LABEL version="1.0"

# ── System deps ────────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        mono-runtime \
        ca-certificates \
        curl \
        unzip \
        python3 \
        python3-pip \
        python3-lxml \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── ThermoRawFileParser (version pinned, overridable at build time) ────────────
ARG TRFP_VERSION=1.4.5
RUN curl -fsSL \
    "https://github.com/compomics/ThermoRawFileParser/releases/download/v${TRFP_VERSION}/ThermoRawFileParser${TRFP_VERSION}.zip" \
    -o /tmp/ThermoRawFileParser.zip \
    && unzip -q /tmp/ThermoRawFileParser.zip -d /opt/ThermoRawFileParser \
    && rm /tmp/ThermoRawFileParser.zip

# ── Pipeline scripts ────────────────────────────────────────────────────────────
COPY split_polarity.py /opt/pipeline/split_polarity.py
COPY run_pipeline.sh   /opt/pipeline/run_pipeline.sh
RUN chmod +x /opt/pipeline/run_pipeline.sh

# ── Volumes ─────────────────────────────────────────────────────────────────────
# /data/raw   → mount your folder of .raw files here (read)
# /data/mzML  → output: interleaved mzML + metadata JSON
# /data/mzML/split → output: _pos.mzML and _neg.mzML per sample
VOLUME ["/data/raw"]

ENTRYPOINT ["/opt/pipeline/run_pipeline.sh"]

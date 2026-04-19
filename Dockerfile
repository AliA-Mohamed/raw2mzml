FROM --platform=linux/amd64 debian:bookworm-slim

LABEL maintainer="AliA-Mohamed"
LABEL description="Convert Thermo .raw files to polarity-split .mzML"
LABEL version="1.0"

# ── System deps ────────────────────────────────────────────────────────────────
# libicu72: required by the self-contained .NET 8 runtime inside ThermoRawFileParser
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        unzip \
        libicu72 \
        python3 \
        python3-lxml \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── ThermoRawFileParser v2.0.0 (self-contained .NET 8 Linux binary, no Mono) ──
RUN curl -fsSL \
    "https://github.com/compomics/ThermoRawFileParser/releases/download/v.2.0.0-dev/ThermoRawFileParser-v.2.0.0-dev-linux.zip" \
    -o /tmp/ThermoRawFileParser.zip \
    && unzip -q /tmp/ThermoRawFileParser.zip -d /opt/ThermoRawFileParser \
    && chmod +x /opt/ThermoRawFileParser/ThermoRawFileParser \
    && rm /tmp/ThermoRawFileParser.zip

# ── Pipeline scripts ────────────────────────────────────────────────────────────
COPY split_polarity.py /opt/pipeline/split_polarity.py
COPY run_pipeline.sh   /opt/pipeline/run_pipeline.sh
RUN chmod +x /opt/pipeline/run_pipeline.sh

# ── Volumes ─────────────────────────────────────────────────────────────────────
# /data/raw        → mount your folder of .raw files here (read)
# /data/raw/mzML   → output: interleaved mzML + metadata JSON
# /data/raw/mzML/split → output: _pos.mzML and _neg.mzML per sample
VOLUME ["/data/raw"]

ENTRYPOINT ["/opt/pipeline/run_pipeline.sh"]

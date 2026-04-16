# raw2mzml

Convert Thermo Orbitrap `.raw` files to polarity-split `.mzML` files using a single Docker command — no local dependencies required.

## Quick Start

```bash
# Build the image (one-time)
docker build -t raw2mzml .

# Run — replace the left side of the colon with your data folder
docker run --rm -v /path/to/your/raw/files:/data/raw raw2mzml
```

Output appears in your folder under `mzML/` and `mzML/split/`.

**New to Docker?** See [HOW_TO_USE.md](HOW_TO_USE.md) for a step-by-step guide (Mac, Windows, Linux) with troubleshooting.

---

## What it does

```
Thermo .raw files
       │
       ▼  Step 1 — ThermoRawFileParser v1.4.5 (Mono)
  .mzML  (indexed mzML, centroided, both polarities combined)
       │
       ▼  Step 2 — split_polarity.py (Python + lxml)
  _pos.mzML  +  _neg.mzML  (one file per polarity per sample)
```

- **Step 1** applies vendor peak picking (Thermo centroiding) and records SHA-1 checksums of source files in each mzML header
- **Step 2** splits on PSI-MS CV terms `MS:1000130` (positive) and `MS:1000129` (negative) — zero polarity cross-contamination
- Works with any Thermo Orbitrap acquisition type (LC-MS, DI-MS, GC-MS)

---

## Output structure

```
your-data-folder/
├── sample_1.raw                 ← original files, untouched
├── sample_2.raw
└── mzML/
    ├── sample_1.mzML            ← converted, both polarities
    ├── sample_1-metadata.json   ← instrument + run metadata
    ├── sample_2.mzML
    ├── sample_2-metadata.json
    └── split/
        ├── sample_1_pos.mzML    ← positive mode only
        ├── sample_1_neg.mzML    ← negative mode only
        ├── sample_2_pos.mzML
        └── sample_2_neg.mzML
```

---

## Files

| File | Purpose |
|---|---|
| `Dockerfile` | Debian slim + Mono + Python 3 + lxml + ThermoRawFileParser v1.4.5 |
| `run_pipeline.sh` | Container entrypoint — validates input, runs both steps, fixes file ownership |
| `split_polarity.py` | Splits interleaved mzML by polarity CV term |
| `docker-compose.yml` | Convenience wrapper — edit volume path, then `docker compose up` |

---

## Options

| Environment variable | Default | Description |
|---|---|---|
| `RAW_DIR` | `/data/raw` | Input directory inside the container |
| `MZML_DIR` | `/data/raw/mzML` | Output directory inside the container |
| `HOST_UID` | UID of mounted folder | Output file ownership on the host |
| `HOST_GID` | GID of mounted folder | Output file group on the host |

Override with `-e`:
```bash
docker run --rm \
  -v /your/data:/data/raw \
  -e HOST_UID=$(id -u) \
  -e HOST_GID=$(id -g) \
  raw2mzml
```

---

## Running without Docker

Requirements: Mono, Python 3 with lxml, ThermoRawFileParser v1.4.5

```bash
# Step 1 — convert
mono /path/to/ThermoRawFileParser.exe \
  -d /path/to/raw \
  -o /path/to/raw/mzML \
  -f 2 -m 0 -l 1

# Step 2 — split
MZML_DIR=/path/to/raw/mzML python3 split_polarity.py
```

---

## License

MIT — see [LICENSE](LICENSE).

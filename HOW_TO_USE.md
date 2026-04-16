# How to Use raw2mzml — Beginner's Guide

> **What this tool does**
> It converts the raw data files from your Thermo mass spectrometer (`.raw` files) into a standard open format called `.mzML`. It also automatically separates positive and negative ion mode data into separate files. Both steps are needed before you can open your data in most mass spec analysis software.
>
> You do **not** need to install Python, Mono, or any other software. Just Docker.

---

## What you need

- A computer (Mac, Windows, or Linux)
- Your `.raw` files in a folder
- About 10 minutes for the one-time setup

---

## Step 1 — Install Docker

Docker is a free tool that runs the converter on any computer without you needing to install anything else.

**Mac:**
1. Go to [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Click **"Download for Mac"** — choose **Apple Chip** if you have an M1/M2/M3/M4 Mac, or **Intel Chip** for older Macs
3. Open the downloaded `.dmg` file and drag Docker to your Applications folder
4. Open Docker from Applications — you'll see a whale icon in your menu bar
5. Wait until it says **"Docker Desktop is running"**

**Windows:**
1. Go to [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Click **"Download for Windows"**
3. Run the installer and follow the prompts (you may need to restart)
4. Open Docker Desktop from the Start menu
5. Wait until it says **"Docker Desktop is running"**

**Linux:**
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in, then verify:
docker run hello-world
```

> **Check Docker is working:** Open a terminal and run `docker --version`. You should see something like `Docker version 27.x.x`.

---

## Step 2 — Get this tool

**Option A — Download as ZIP (no git needed):**
1. Go to [https://github.com/AliA-Mohamed/raw2mzml](https://github.com/AliA-Mohamed/raw2mzml)
2. Click the green **"Code"** button → **"Download ZIP"**
3. Unzip the file somewhere easy to find (e.g. your Desktop)

**Option B — Clone with git:**
```bash
git clone https://github.com/AliA-Mohamed/raw2mzml.git
cd raw2mzml
```

---

## Step 3 — Build the Docker image (one-time)

Open a terminal, navigate to the `raw2mzml` folder you downloaded, and run:

```bash
docker build -t raw2mzml .
```

This downloads and installs everything inside the container. It takes a few minutes the first time. You only need to do this once.

---

## Step 4 — Run the conversion

Replace the path before `:/data/raw` with the path to your folder of `.raw` files.

**Mac / Linux:**
```bash
docker run --rm -v /path/to/your/data:/data/raw raw2mzml
```

**Windows (PowerShell):**
```powershell
docker run --rm -v C:\Users\YourName\your-data:/data/raw raw2mzml
```

**Windows (Command Prompt):**
```cmd
docker run --rm -v C:/Users/YourName/your-data:/data/raw raw2mzml
```

**How to find your path:**
- **Mac:** Drag the folder from Finder into your terminal window — it pastes the path automatically
- **Windows:** In File Explorer, click the address bar at the top of the window to see and copy the path

---

## Step 5 — Find your results

After you see `✓ Pipeline complete`, look inside your data folder for a new `mzML/` folder:

```
your-data-folder/
├── sample_1.raw          ← unchanged
├── sample_2.raw
└── mzML/
    ├── sample_1.mzML            ← converted (both polarities)
    ├── sample_1-metadata.json
    └── split/
        ├── sample_1_pos.mzML    ← positive mode only
        ├── sample_1_neg.mzML    ← negative mode only
        └── ...
```

Use the files in `mzML/split/` as input to your mass spec analysis software. Load all `_pos.mzML` files together for positive mode analysis, and all `_neg.mzML` files for negative mode.

---

## Troubleshooting

**"Docker is not running"**
Open Docker Desktop and wait until it shows a green running status before retrying.

**"No .raw files found"**
The path you gave doesn't contain `.raw` files at the top level. Double-check you are pointing to the right folder.

**Output files are owned by root**
Add your user ID to the command:
```bash
docker run --rm \
  -v /your/data:/data/raw \
  -e HOST_UID=$(id -u) \
  -e HOST_GID=$(id -g) \
  raw2mzml
```

**"Unable to find image 'raw2mzml:latest'"**
You haven't built the image yet. Run `docker build -t raw2mzml .` from the `raw2mzml` folder first.

**The command seems stuck**
The first file can take 10–30 seconds to start. Large files take longer. As long as there is no error message, it is working.

---

## FAQ

**Do I need Python, Mono, or conda installed?**
No. Everything runs inside Docker.

**Does this work on Windows?**
Yes — Mac (Apple Silicon and Intel), Windows, and Linux are all supported.

**How long does it take?**
Around 2–5 seconds per file for conversion plus a few seconds for splitting. A batch of 16 files typically completes in under 2 minutes.

**Does it work for LC-MS data, not just DI-MS?**
Yes. The conversion and polarity splitting work for any Thermo Orbitrap `.raw` file regardless of acquisition mode.

**Something went wrong and I don't understand the error.**
Open an issue at [https://github.com/AliA-Mohamed/raw2mzml/issues](https://github.com/AliA-Mohamed/raw2mzml/issues) and paste the full terminal output.

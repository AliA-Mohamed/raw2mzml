#!/usr/bin/env python3
"""
Split mzML files by polarity into separate positive and negative mode files.

CV terms:
  MS:1000130 = positive scan
  MS:1000129 = negative scan

Usage:
  python3 split_polarity.py                        # process all mzML in ./mzML/
  python3 split_polarity.py file1.mzML file2.mzML  # process specific files
"""

import sys
import os
import glob
from lxml import etree

# Polarity CV accessions
POS_CV = "MS:1000130"  # positive scan
NEG_CV = "MS:1000129"  # negative scan

NS = "http://psi.hupo.org/ms/mzml"
NS_MAP = {"ms": NS}


def strip_ns(tag):
    """Return tag without namespace prefix."""
    return tag.split("}")[-1] if "}" in tag else tag


def get_polarity(spectrum_elem):
    """Return 'pos', 'neg', or None for a <spectrum> element."""
    for cv in spectrum_elem.iter(f"{{{NS}}}cvParam"):
        acc = cv.get("accession", "")
        if acc == POS_CV:
            return "pos"
        if acc == NEG_CV:
            return "neg"
    return None


def split_mzml(input_path, output_dir):
    """Split a single mzML file into _pos.mzML and _neg.mzML."""
    basename = os.path.splitext(os.path.basename(input_path))[0]

    print(f"  Parsing {basename}.mzML ...", end=" ", flush=True)
    tree = etree.parse(input_path)
    root = tree.getroot()

    # Handle both indexedmzML wrapper and plain mzML root
    if strip_ns(root.tag) == "indexedmzML":
        mzml_elem = root.find(f"{{{NS}}}mzML")
    else:
        mzml_elem = root

    # Locate the spectrumList
    run_elem = mzml_elem.find(f".//{{{NS}}}run")
    spectrum_list = run_elem.find(f"{{{NS}}}spectrumList")

    if spectrum_list is None:
        print("no spectrumList found, skipping.")
        return

    # Partition spectra by polarity
    pos_spectra = []
    neg_spectra = []
    skipped = 0

    for spec in spectrum_list:
        pol = get_polarity(spec)
        if pol == "pos":
            pos_spectra.append(spec)
        elif pol == "neg":
            neg_spectra.append(spec)
        else:
            skipped += 1

    print(f"pos={len(pos_spectra)}, neg={len(neg_spectra)}, skipped={skipped}")

    for polarity, spectra, suffix in [("positive", pos_spectra, "pos"),
                                       ("negative", neg_spectra, "neg")]:
        if not spectra:
            print(f"    [{suffix}] no spectra, skipping.")
            continue

        out_path = os.path.join(output_dir, f"{basename}_{suffix}.mzML")

        # Deep-copy the full mzML element tree
        new_mzml = etree.fromstring(etree.tostring(mzml_elem))

        # Update fileContent to reflect single polarity
        file_content = new_mzml.find(
            f".//{{{NS}}}fileContent"
        )
        if file_content is not None:
            for cv in list(file_content):
                acc = cv.get("accession", "")
                if acc in (POS_CV, NEG_CV):
                    file_content.remove(cv)
            pol_cv = etree.SubElement(file_content, f"{{{NS}}}cvParam")
            if suffix == "pos":
                pol_cv.set("cvRef", "MS")
                pol_cv.set("accession", POS_CV)
                pol_cv.set("name", "positive scan")
                pol_cv.set("value", "")
            else:
                pol_cv.set("cvRef", "MS")
                pol_cv.set("accession", NEG_CV)
                pol_cv.set("name", "negative scan")
                pol_cv.set("value", "")

        # Replace spectrumList with filtered spectra
        new_run = new_mzml.find(f".//{{{NS}}}run")
        new_sl = new_run.find(f"{{{NS}}}spectrumList")
        # Remove all existing spectra
        for child in list(new_sl):
            new_sl.remove(child)

        # Re-index and add filtered spectra
        new_sl.set("count", str(len(spectra)))
        for i, spec in enumerate(spectra):
            spec_copy = etree.fromstring(etree.tostring(spec))
            spec_copy.set("index", str(i))
            new_sl.append(spec_copy)

        # Write as plain mzML (not indexed — MS-DIAL handles both)
        out_tree = etree.ElementTree(new_mzml)
        with open(out_path, "wb") as fh:
            out_tree.write(
                fh,
                xml_declaration=True,
                encoding="utf-8",
                pretty_print=True,
            )
        size_mb = os.path.getsize(out_path) / 1024 / 1024
        print(f"    [{suffix}] {len(spectra)} spectra → {basename}_{suffix}.mzML ({size_mb:.1f} MB)")


def main():
    # MZML_DIR env var is set by the Docker entrypoint (run_pipeline.sh).
    # Falls back to a sibling mzML/ directory when run locally.
    default_mzml = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mzML")
    mzml_dir = os.environ.get("MZML_DIR", default_mzml)
    split_dir = os.path.join(mzml_dir, "split")
    os.makedirs(split_dir, exist_ok=True)

    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        # All mzML in the mzML/ directory (not already split files)
        files = sorted(
            f for f in glob.glob(os.path.join(mzml_dir, "*.mzML"))
            if not (f.endswith("_pos.mzML") or f.endswith("_neg.mzML"))
        )

    if not files:
        print("No mzML files found.")
        sys.exit(1)

    print(f"Splitting {len(files)} file(s) → {split_dir}/\n")
    for f in files:
        split_mzml(f, split_dir)

    print(f"\nDone. Split files in: {split_dir}/")


if __name__ == "__main__":
    main()

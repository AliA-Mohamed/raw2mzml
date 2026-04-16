#!/usr/bin/env python3
"""
Split mzML files by polarity into separate positive and negative mode files.

CV terms:
  MS:1000130 = positive scan
  MS:1000129 = negative scan

Usage:
  python3 split_polarity.py                          # all *.mzML in MZML_DIR or ./mzML/
  python3 split_polarity.py file1.mzML file2.mzML    # specific files
  python3 split_polarity.py -o /out/dir file.mzML    # custom output directory
  python3 split_polarity.py --help
"""

import argparse
import glob
import os
import sys

from lxml import etree

# Polarity CV accessions
POS_CV = "MS:1000130"  # positive scan
NEG_CV = "MS:1000129"  # negative scan

NS = "http://psi.hupo.org/ms/mzml"


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
    """Split a single mzML file into _pos.mzML and _neg.mzML.

    Uses in-place tree mutation to avoid deep-copying the full DOM twice,
    keeping peak memory close to 1× the file size rather than 3×.
    """
    basename = os.path.splitext(os.path.basename(input_path))[0]
    print(f"  Parsing {basename}.mzML ...", end=" ", flush=True)

    try:
        tree = etree.parse(input_path)
    except etree.XMLSyntaxError as exc:
        print(f"\n  [WARN] skipping {basename}.mzML — malformed XML: {exc}",
              file=sys.stderr)
        return

    root = tree.getroot()
    mzml_elem = root.find(f"{{{NS}}}mzML") if strip_ns(root.tag) == "indexedmzML" else root
    run_elem = mzml_elem.find(f".//{{{NS}}}run")
    spectrum_list = run_elem.find(f"{{{NS}}}spectrumList") if run_elem is not None else None

    if spectrum_list is None:
        print("no spectrumList found, skipping.")
        return

    # Classify by polarity — element references, no copies
    all_spectra = list(spectrum_list)
    pos_spectra = [s for s in all_spectra if get_polarity(s) == "pos"]
    neg_spectra = [s for s in all_spectra if get_polarity(s) == "neg"]
    skipped = len(all_spectra) - len(pos_spectra) - len(neg_spectra)
    print(f"pos={len(pos_spectra)}, neg={len(neg_spectra)}, skipped={skipped}")

    # Save and strip existing polarity cvParams from fileContent so we can
    # inject the correct single-polarity one per output file.
    file_content = mzml_elem.find(f".//{{{NS}}}fileContent")
    saved_pol_cvs = []
    if file_content is not None:
        saved_pol_cvs = [
            cv for cv in list(file_content)
            if cv.get("accession", "") in (POS_CV, NEG_CV)
        ]
        for cv in saved_pol_cvs:
            file_content.remove(cv)

    for polarity_spectra, suffix, acc, pol_name in [
        (pos_spectra, "pos", POS_CV, "positive scan"),
        (neg_spectra, "neg", NEG_CV, "negative scan"),
    ]:
        if not polarity_spectra:
            print(f"    [{suffix}] no spectra, skipping.")
            continue

        out_path = os.path.join(output_dir, f"{basename}_{suffix}.mzML")

        # Detach all spectra, attach only the filtered set (re-indexed)
        for s in list(spectrum_list):
            spectrum_list.remove(s)
        spectrum_list.set("count", str(len(polarity_spectra)))
        for i, s in enumerate(polarity_spectra):
            s.set("index", str(i))
            spectrum_list.append(s)

        # Inject polarity cvParam into fileContent
        pol_cv = None
        if file_content is not None:
            pol_cv = etree.SubElement(file_content, f"{{{NS}}}cvParam")
            pol_cv.set("cvRef", "MS")
            pol_cv.set("accession", acc)
            pol_cv.set("name", pol_name)
            pol_cv.set("value", "")

        etree.ElementTree(mzml_elem).write(
            out_path, xml_declaration=True, encoding="utf-8", pretty_print=True
        )
        size_mb = os.path.getsize(out_path) / 1024 / 1024
        print(f"    [{suffix}] {len(polarity_spectra)} spectra → "
              f"{basename}_{suffix}.mzML ({size_mb:.1f} MB)")

        # Undo mutations before the next polarity pass
        for s in list(spectrum_list):
            spectrum_list.remove(s)
        if pol_cv is not None:
            file_content.remove(pol_cv)

    # Restore original tree state
    spectrum_list.set("count", str(len(all_spectra)))
    for s in all_spectra:
        spectrum_list.append(s)
    if file_content is not None:
        for cv in saved_pol_cvs:
            file_content.append(cv)


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "files", nargs="*", metavar="FILE",
        help="mzML files to process (default: all *.mzML in MZML_DIR or ./mzML/)",
    )
    parser.add_argument(
        "--output-dir", "-o", metavar="DIR",
        help="directory for split output files (default: <input_dir>/split/)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Resolve input files
    if args.files:
        files = args.files
        default_mzml = os.path.dirname(os.path.abspath(args.files[0]))
    else:
        # MZML_DIR env var is set by the Docker entrypoint.
        # Falls back to a sibling mzML/ directory when run locally.
        default_mzml = os.environ.get(
            "MZML_DIR",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "mzML"),
        )
        files = sorted(
            f for f in glob.glob(os.path.join(default_mzml, "*.mzML"))
            if not (f.endswith("_pos.mzML") or f.endswith("_neg.mzML"))
        )

    if not files:
        print("No mzML files found.", file=sys.stderr)
        sys.exit(1)

    # Resolve output directory
    if args.output_dir:
        split_dir = args.output_dir
    else:
        split_dir = os.path.join(default_mzml, "split")

    os.makedirs(split_dir, exist_ok=True)

    print(f"Splitting {len(files)} file(s) → {split_dir}/\n")
    for f in files:
        split_mzml(f, split_dir)

    print(f"\nDone. Split files in: {split_dir}/")


if __name__ == "__main__":
    main()

import os
import sys

import pytest
from lxml import etree

# Ensure the repo root is importable regardless of where pytest is invoked from
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from split_polarity import NS, NEG_CV, POS_CV, split_mzml

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "mixed.mzML")


def test_output_files_created(tmp_path):
    split_mzml(FIXTURE, str(tmp_path))
    assert (tmp_path / "mixed_pos.mzML").exists()
    assert (tmp_path / "mixed_neg.mzML").exists()


def test_pos_spectrum_count(tmp_path):
    split_mzml(FIXTURE, str(tmp_path))
    tree = etree.parse(str(tmp_path / "mixed_pos.mzML"))
    spectra = tree.findall(f".//{{{NS}}}spectrum")
    assert len(spectra) == 2


def test_neg_spectrum_count(tmp_path):
    split_mzml(FIXTURE, str(tmp_path))
    tree = etree.parse(str(tmp_path / "mixed_neg.mzML"))
    spectra = tree.findall(f".//{{{NS}}}spectrum")
    assert len(spectra) == 1


def test_pos_spectra_reindexed(tmp_path):
    split_mzml(FIXTURE, str(tmp_path))
    tree = etree.parse(str(tmp_path / "mixed_pos.mzML"))
    indices = [s.get("index") for s in tree.findall(f".//{{{NS}}}spectrum")]
    assert indices == ["0", "1"]


def test_pos_filecontent_cv(tmp_path):
    split_mzml(FIXTURE, str(tmp_path))
    tree = etree.parse(str(tmp_path / "mixed_pos.mzML"))
    fc = tree.find(f".//{{{NS}}}fileContent")
    accs = {cv.get("accession") for cv in fc}
    assert POS_CV in accs
    assert NEG_CV not in accs


def test_neg_filecontent_cv(tmp_path):
    split_mzml(FIXTURE, str(tmp_path))
    tree = etree.parse(str(tmp_path / "mixed_neg.mzML"))
    fc = tree.find(f".//{{{NS}}}fileContent")
    accs = {cv.get("accession") for cv in fc}
    assert NEG_CV in accs
    assert POS_CV not in accs


def test_malformed_xml_skipped(tmp_path, capsys):
    bad = tmp_path / "bad.mzML"
    bad.write_text("<broken xml")
    split_mzml(str(bad), str(tmp_path))  # must not raise
    captured = capsys.readouterr()
    assert "WARN" in captured.err


def test_no_polarity_spectra_no_output(tmp_path):
    nopol = tmp_path / "nopol.mzML"
    nopol.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<mzML xmlns="http://psi.hupo.org/ms/mzml">\n'
        "  <fileDescription><fileContent/></fileDescription>\n"
        "  <run>\n"
        '    <spectrumList count="1" defaultDataProcessingRef="dp1">\n'
        '      <spectrum index="0" id="scan=1" defaultArrayLength="0"/>\n'
        "    </spectrumList>\n"
        "  </run>\n"
        "</mzML>"
    )
    split_mzml(str(nopol), str(tmp_path))
    assert not (tmp_path / "nopol_pos.mzML").exists()
    assert not (tmp_path / "nopol_neg.mzML").exists()

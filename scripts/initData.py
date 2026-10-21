import subprocess
import sys
import tarfile
from pathlib import Path
from urllib.request import urlretrieve

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from configs.app import Config


def getNuminaMath() -> Path:
    """Download NuminaMath at the revision specified in Config."""
    output_dir = Config.NUMINA_OUTPUT_DIR
    print(f"NuminaMath: {Config.NUMINA_REPO_ID} @ {Config.NUMINA_REVISION}", flush=True)
    subprocess.run(
        ["hf", "download", Config.NUMINA_REPO_ID,
         "--repo-type", Config.NUMINA_REPO_TYPE, "--revision", Config.NUMINA_REVISION,
         "--local-dir", str(output_dir)],
        check=True,
    )
    return output_dir


def getProofNet() -> Path:
    output_dir = Config.PROOFNET_OUTPUT_DIR
    print(f"ProofNet: {Config.PROOFNET_REPO_URL} @ {Config.PROOFNET_REVISION}", flush=True)
    subprocess.run(
        ["git", "clone", "--no-checkout", Config.PROOFNET_REPO_URL, str(output_dir)],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(output_dir), "checkout", "--detach", Config.PROOFNET_REVISION],
        check=True,
    )
    return output_dir

def getLeanDojo() -> Path:
    """Tải phiên bản LeanDojo được chỉ định trong Config."""
    output_dir = Config.LEANDOJO_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / Config.LEANDOJO_ARCHIVE_NAME

    print(
        f"LeanDojo: {Config.LEANDOJO_URL}\n"
        f"Phiên bản: {Config.LEANDOJO_VERSION}; mathlib: {Config.LEANDOJO_MATHLIB_REVISION}",
        flush=True,
    )
    urlretrieve(Config.LEANDOJO_URL, archive)

    print("Đang giải nén...", flush=True)
    with tarfile.open(archive, "r:gz") as data:
        data.extractall(output_dir, filter="data")

    return output_dir

getLeanDojo()

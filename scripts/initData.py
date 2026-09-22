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
    output_dir = Config.RAW_DATA / "numinaMath"
    subprocess.run(
        ["hf", "download", Config.NUMINA_REPO_ID,
         "--repo-type", "dataset", "--revision", Config.NUMINA_REVISION,
         "--local-dir", str(output_dir)],
        check=True,
    )
    return output_dir
# Data in benchmark_to_publish folder
def getProofNet() -> Path:
    output_dir = Config.RAW_DATA / "proofNet"
    subprocess.run(["git", "clone", "https://github.com/zhangir-azerbayev/ProofNet", str(output_dir)])
    return output_dir

def getLeanDojo() -> Path:
    """Tải Benchmark 4 v10, mathlib4 commit 29dcec074de168ac2bf835a77ef68bbe069194c5."""
    output_dir = Config.RAW_DATA / "leandojoBenchmark4v10"
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / "leandojo_benchmark_4.tar.gz"
    url = "https://zenodo.org/records/12740403/files/leandojo_benchmark_4.tar.gz?download=1"

    print("Đang tải LeanDojo Benchmark 4 v10...", flush=True)
    urlretrieve(url, archive)

    print("Đang giải nén...", flush=True)
    with tarfile.open(archive, "r:gz") as data:
        data.extractall(output_dir, filter="data")

    return output_dir

getLeanDojo()
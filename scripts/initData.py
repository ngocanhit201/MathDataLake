import subprocess
import sys
from pathlib import Path

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

getProofNet()
from pathlib import Path


class Config:
    ROOT = Path(__file__).resolve().parents[1]
    RAW_DATA = ROOT / "results/raw"
    NUMINA_REPO_ID = "AI-MO/NuminaMath-CoT"
    NUMINA_REVISION = "9d8d210c9f6a36c8f3cd84045668c9b7800ef517"
    NUMINA_REPO_TYPE = "dataset"
    NUMINA_OUTPUT_DIR = RAW_DATA / "numinaMath"

    PROOFNET_REPO_URL = "https://github.com/zhangir-azerbayev/ProofNet"
    PROOFNET_REVISION = "509ad79710ed4f46ff5c282ed5640c1aa9ac3f30"
    PROOFNET_OUTPUT_DIR = RAW_DATA / "proofNet"

    LEANDOJO_URL = "https://zenodo.org/records/12740403/files/leandojo_benchmark_4.tar.gz?download=1"
    LEANDOJO_VERSION = "Benchmark 4 v10"
    LEANDOJO_MATHLIB_REVISION = "29dcec074de168ac2bf835a77ef68bbe069194c5"
    LEANDOJO_ARCHIVE_NAME = "leandojo_benchmark_4.tar.gz"
    LEANDOJO_OUTPUT_DIR = RAW_DATA / "leandojoBenchmark4v10"

from pathlib import Path


class Config:
    ROOT = Path(__file__).resolve().parents[1]
    RAW_DATA = ROOT / "results/raw"
    NUMINA_REPO_ID = "AI-MO/NuminaMath-CoT"
    NUMINA_REVISION = "9d8d210c9f6a36c8f3cd84045668c9b7800ef517"
    

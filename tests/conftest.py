from pathlib import Path
import pytest


@pytest.fixture(scope="session")
def detector_url() -> str:
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def golden_dir() -> Path:
    return Path(__file__).parent / "golden"

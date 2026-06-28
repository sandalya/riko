import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path so project modules (bot, agent, mcp, core) are importable.
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def detector_url() -> str:
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def golden_dir() -> Path:
    return Path(__file__).parent / "golden"

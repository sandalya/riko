import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

# Ensure project root is on sys.path so project modules (bot, agent, mcp, core) are importable.
sys.path.insert(0, str(Path(__file__).parent.parent))

_PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def mcp_server() -> ModuleType:
    """Load mcp/server.py by explicit path — avoids PyPI mcp package shadowing."""
    server_path = _PROJECT_ROOT / "mcp" / "server.py"
    spec = importlib.util.spec_from_file_location("_drone_recon_mcp_server", server_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def detector_url() -> str:
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def golden_dir() -> Path:
    return Path(__file__).parent / "golden"

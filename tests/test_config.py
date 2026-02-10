"""Test configuration."""
import os
import pytest
from pathlib import Path


def test_project_structure():
    """Test that all important files exist in the new architecture."""
    project_root = Path(__file__).parent.parent

    important_files = [
        "pyproject.toml",
        "README.md",
        "src/main.py",
        # Shared
        "src/shared/config.py",
        "src/shared/models.py",
        "src/shared/schemas.py",
        "src/shared/database.py",
        # Core plugin system
        "src/core/plugin/interface.py",
        "src/core/plugin/base.py",
        "src/core/plugin/manager.py",
        # Plugins
        "src/core/plugins/finance/plugin.py",
        "src/core/plugins/work/plugin.py",
        # Routing
        "src/routing/router.py",
        # Access layer
        "src/access/base.py",
        "src/access/cli/adapter.py",
        "src/access/cli/commands.py",
        # Storage
        "src/storage/interfaces.py",
        "src/storage/repositories/base.py",
        "src/storage/repositories/finance_repo.py",
        "src/storage/repositories/work_repo.py",
        "src/storage/context/repository.py",
        # Prompts
        "prompts/router_decision.txt",
        "prompts/parse_finance.txt",
        "prompts/parse_work.txt",
    ]

    missing_files = []
    for file_path in important_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)

    if missing_files:
        pytest.fail(f"Missing files: {', '.join(missing_files)}")


def test_config_loading():
    """Test that configuration can be loaded."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        from src.shared.config import settings
        assert hasattr(settings, "ai_provider")
        assert hasattr(settings, "database_url")
    except Exception as e:
        pytest.fail(f"Configuration loading failed: {e}")


if __name__ == "__main__":
    test_project_structure()
    test_config_loading()
    print("\n[OK] All basic tests passed!")

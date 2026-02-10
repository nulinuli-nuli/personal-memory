"""Simple test verification script (doesn't require pytest)."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def verify_test_files_exist():
    """Verify all test files exist."""
    test_files = [
        "tests/core/plugins/test_finance_plugin.py",
        "tests/core/plugins/test_work_plugin.py",
        "tests/core/test_plugin_manager.py",
        "tests/routing/test_router.py",
        "tests/storage/test_context_repository.py",
        "tests/integration/test_cli_e2e.py",
        "tests/conftest.py",
    ]

    print("检查测试文件...")
    all_exist = True
    for test_file in test_files:
        path = Path(__file__).parent.parent / test_file
        if path.exists():
            print(f"  ✅ {test_file}")
        else:
            print(f"  ❌ {test_file} - 不存在")
            all_exist = False

    return all_exist


def verify_test_imports():
    """Verify test modules can be imported."""
    print("\n检查测试模块导入...")

    try:
        from tests.core.plugins.test_finance_plugin import test_plugin_properties
        print("  ✅ Finance plugin tests 导入成功")
    except Exception as e:
        print(f"  ❌ Finance plugin tests 导入失败: {e}")
        return False

    try:
        from tests.core.plugins.test_work_plugin import test_plugin_properties
        print("  ✅ Work plugin tests 导入成功")
    except Exception as e:
        print(f"  ❌ Work plugin tests 导入失败: {e}")
        return False

    try:
        from tests.routing.test_router import test_route_to_finance_plugin
        print("  ✅ Router tests 导入成功")
    except Exception as e:
        print(f"  ❌ Router tests 导入失败: {e}")
        return False

    try:
        from tests.core.test_plugin_manager import test_discover_plugins
        print("  ✅ Plugin manager tests 导入成功")
    except Exception as e:
        print(f"  ❌ Plugin manager tests 导入失败: {e}")
        return False

    try:
        from tests.storage.test_context_repository import test_get_context_found
        print("  ✅ Context repository tests 导入成功")
    except Exception as e:
        print(f"  ❌ Context repository tests 导入失败: {e}")
        return False

    return True


def verify_test_structure():
    """Verify test structure is correct."""
    print("\n检查测试结构...")

    required_dirs = [
        "tests/core/plugins",
        "tests/routing",
        "tests/storage",
        "tests/integration"
    ]

    all_exist = True
    for dir_path in required_dirs:
        path = Path(__file__).parent.parent / dir_path
        if path.exists() and path.is_dir():
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/ - 不存在")
            all_exist = False

    return all_exist


def main():
    """Run all verifications."""
    print("=" * 60)
    print("Personal Memory - 测试验证脚本")
    print("=" * 60)

    results = []

    # Verify files
    results.append(("测试文件存在性", verify_test_files_exist()))

    # Verify structure
    results.append(("测试目录结构", verify_test_structure()))

    # Verify imports
    results.append(("测试模块导入", verify_test_imports()))

    # Summary
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 所有验证通过！测试已准备就绪。")
        print("\n运行测试:")
        print("  pytest tests/")
        print("\n或安装 pytest:")
        print("  pip install pytest pytest-asyncio")
        return 0
    else:
        print("\n⚠️  部分验证失败，请检查上述错误。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

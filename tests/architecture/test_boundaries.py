import ast
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "src"
SHOP = SOURCE / "shop"
APPLICATION = SOURCE / "bootstrap" / "application"
WEB_FRAMEWORKS = {"fastapi", "litestar", "blacksheep", "starlette", "msgspec", "rodi"}
FRAMEWORK_FOLDERS = {
    "fastapi": {"fastapi"},
    "litestar": {"litestar", "msgspec"},
    "blacksheep": {"blacksheep", "rodi"},
}


def _imports(directory: Path) -> dict[Path, set[str]]:
    found: dict[Path, set[str]] = {}
    for path in directory.rglob("*.py"):
        modules: set[str] = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules.add(node.module)
        found[path] = modules
    return found


def _violations(directory: Path, forbidden: set[str]) -> list[str]:
    assert directory.is_dir(), f"{directory} does not exist"
    return [
        f"{path.relative_to(SOURCE)} imports {module}"
        for path, modules in _imports(directory).items()
        for module in modules
        if any(module == prefix or module.startswith(f"{prefix}.") for prefix in forbidden)
    ]


def test_the_domain_imports_nothing_from_the_outer_layers_or_any_framework() -> None:
    forbidden = WEB_FRAMEWORKS | {
        "pydantic",
        "pycraftcore",
        "shop.application",
        "shop.adapter",
        "bootstrap",
    }
    assert _violations(SHOP / "domain", forbidden) == []


def test_the_application_depends_only_on_the_domain() -> None:
    forbidden = WEB_FRAMEWORKS | {"pydantic", "pycraftcore", "shop.adapter", "bootstrap"}
    assert _violations(SHOP / "application", forbidden) == []


def test_the_shop_imports_no_web_framework_and_never_the_composition_root() -> None:
    assert _violations(SHOP, WEB_FRAMEWORKS | {"bootstrap", "shop_benchmark"}) == []


@pytest.mark.parametrize("framework", sorted(FRAMEWORK_FOLDERS))
def test_each_framework_folder_imports_only_its_own_framework(framework) -> None:
    others = WEB_FRAMEWORKS - FRAMEWORK_FOLDERS[framework]
    assert _violations(APPLICATION / framework, others) == []


def test_web_frameworks_are_imported_only_in_their_folders() -> None:
    folders = tuple(f"{(APPLICATION / name).relative_to(SOURCE)}/" for name in FRAMEWORK_FOLDERS)
    outside = [
        violation
        for violation in _violations(SOURCE / "bootstrap", WEB_FRAMEWORKS)
        if not violation.startswith(folders)
    ]
    assert outside == []


def test_the_benchmark_never_imports_the_shop() -> None:
    assert _violations(SOURCE / "shop_benchmark", {"shop", "bootstrap"}) == []

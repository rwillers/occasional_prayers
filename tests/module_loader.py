from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def load_script_module(script_name: str) -> ModuleType:
    root = Path(__file__).resolve().parents[1]
    script_path = root / "scripts" / f"{script_name}.py"
    spec = importlib.util.spec_from_file_location(f"script_{script_name}", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module for {script_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

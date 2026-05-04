# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import sys
import runpy
from pathlib import Path
import pytest

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
example_files = [f for f in EXAMPLES_DIR.glob("**/*.py") if f.name != "__init__.py"]

example_files = [f for f in example_files if "scip" not in f.name]

if sys.version_info >= (3, 13) and sys.version_info < (3, 14):
    example_files = [f for f in example_files if "iis_cplex" not in f.name]


@pytest.mark.parametrize(
    "example_file",
    example_files,
    ids=[f.name for f in example_files]
)
def test_example(example_file):
    try:
        runpy.run_path(str(example_file), run_name="__main__")
    except Exception as e:
        pytest.fail(f"Running {example_file.name} failed with {e}")

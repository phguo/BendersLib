# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from abc import ABCMeta

from ._base import SolverBase, SolverCPBase


def _create_placeholder_solver(name: str, install_message: str):
    """Dynamically creates a placeholder solver class.

    This function is used to create a dummy solver class when the actual
    solver library is not installed. The created class inherits from
    `SolverBase` and raises an `ImportError` upon instantiation,
    prompting the user to install the required package.

    It also implements dummy versions of all abstract methods defined in
    `SolverBase` to ensure that the placeholder class can be created
    without `TypeError`s for un-implemented abstract methods.
    """

    def __init__(self, *args, **kwargs):
        # pylint: disable=super-init-not-called
        raise ImportError(
            f"<{name}> is not installed. {install_message}"
        )

    def dummy_method(*args, **kwargs):
        pass

    class_attrs = {
        '__init__': __init__,
        '__doc__': f"Placeholder for the '{name}' solver. Raises ImportError on instantiation."
    }

    if isinstance(SolverBase, ABCMeta) and hasattr(SolverBase, '__abstractmethods__'):
        for method_name in SolverBase.__abstractmethods__:
            class_attrs[method_name] = dummy_method

    PlaceholderSolver = type(name, (SolverBase,), class_attrs)
    return PlaceholderSolver


try:
    from ._gurobi import Gurobi
except ImportError:  # pragma: no cover
    Gurobi = _create_placeholder_solver("Gurobi", "Install it via 'pip install gurobipy'.")

try:
    from ._copt import Copt
except ImportError:  # pragma: no cover
    Copt = _create_placeholder_solver("Copt", "Install it via 'pip install coptpy'.")

try:
    from ._pyomo import Pyomo
except ImportError:  # pragma: no cover
    Pyomo = _create_placeholder_solver("Pyomo", "Install it via 'pip install pyomo'.")

try:
    from ._scip import Scip
except ImportError:  # pragma: no cover
    Scip = _create_placeholder_solver("Scip", "Install it via 'pip install pyscipopt'.")

try:
    from ._cplex import Cplex
except ImportError:  # pragma: no cover
    Cplex = _create_placeholder_solver("Cplex", "Install it via 'pip install cplex'.")

try:
    from ._ortools import Ortools
except ImportError:  # pragma: no cover
    Ortools = _create_placeholder_solver("Ortools", "Install it via 'pip install ortools'.")

try:
    from ._cplexcp import CplexCP
except ImportError:  # pragma: no cover
    CplexCP = _create_placeholder_solver("CplexCP", "Install it via 'pip install docplex'.")

__all__ = [
    "SolverBase",
    "SolverCPBase",
    "Gurobi",
    "Copt",
    "Pyomo",
    "Scip",
    "Cplex",
    "Ortools",
    "CplexCP",
]

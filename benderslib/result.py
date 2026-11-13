# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import json
import math
from dataclasses import dataclass, field, asdict

from .consts import BendersConsts as CST


@dataclass
class BendersResult:
    """Results and statistics from the Benders Decomposition process.

    Example
    -----------

    .. code-block:: python

        BD = BendersSolver(...)
        BD.solve()
        print(BD.result.obj)
    """

    lb: float = -float('Inf')
    """Lower bound on the objective value."""
    lb_list: list = field(default_factory=list)
    """List of lower bounds over iterations."""
    ub: float = float('Inf')
    """Upper bound on the objective value."""
    ub_list: list = field(default_factory=list)
    """List of upper bounds over iterations."""
    obj: float = float('Inf')
    """Best objective value found."""
    obj_list: list = field(default_factory=list)
    """List of objective values of incumbent solutions found over iterations."""
    gap_abs: float = float('Inf')
    """Absolute gap between upper and lower bounds, defined as ``abs(ub - lb)``."""
    gap: float = float('Inf')
    """Relative gap between upper and lower bounds, defined as ``abs(ub - lb) / abs(ub)``."""
    n_sol: int = 0
    """Number of feasible solutions found."""
    n_iter: int = 0
    """Number of Benders iterations performed."""
    runtime: float = 0.0
    """Total runtime of the Benders decomposition process."""
    runtime_master: float = 0.0
    """Total runtime spent solving the master problem."""
    runtime_sub: float = 0.0
    """Total runtime spent solving the subproblem."""
    n_opt_cuts: int = 0
    """Number of optimality cuts added."""
    n_feas_cuts: int = 0
    """Number of feasibility cuts added."""
    n_cuts: int = 0
    """Total number of optimality cuts and feasibility cuts added."""
    solution: dict = field(default_factory=dict)
    """Dictionary of variable names to their values in the best solution found."""
    status: str = CST.UNSOLVED
    """Final status of the Benders decomposition process, see :class:`BendersConsts` for possible values."""

    def save(self, filename: str) -> None:
        """Save the result to a JSON file.

        Non-finite floating-point values are exported as ``null``.

        Parameters
        -----------

        filename : str
            Path to the JSON file where the result will be saved.
        """
        def json_value(value):
            if isinstance(value, float) and not math.isfinite(value):
                return None
            if isinstance(value, dict):
                return {k: json_value(v) for k, v in value.items()}
            if isinstance(value, (list, tuple)):
                return [json_value(v) for v in value]
            return value

        with open(filename, 'w') as f:
            data = asdict(self)
            if self.solution:
                is_nested = isinstance(next(iter(self.solution.values())), dict)
                if is_nested:
                    data['solution'] = {
                        s: {k: v for k, v in sol.items() if v != 0.0}
                        for s, sol in self.solution.items()
                    }
                else:
                    data['solution'] = {k: v for k, v in self.solution.items() if v != 0.0}
            json.dump(json_value(data), f, indent=4, allow_nan=False)

    def __str__(self):
        summary = (
            f"Benders Result:\n"
            f"  - {'Status:'.ljust(CST.LOG_NAME_WIDTH)}{self.status}\n"
            f"  - {'Incumbent:'.ljust(CST.LOG_NAME_WIDTH)}{self.obj:.10e}\n"
            f"  - {'Bound:'.ljust(CST.LOG_NAME_WIDTH)}{self.lb:.10e}\n"
            f"  - {'Gap (abs.):'.ljust(CST.LOG_NAME_WIDTH)}{self.gap_abs:.10f}\n"
            f"  - {'Gap (rel.):'.ljust(CST.LOG_NAME_WIDTH)}{self.gap:.8%}\n"
            f"  - {'Solutions No.:'.ljust(CST.LOG_NAME_WIDTH)}{self.n_sol}\n"
            f"  - {'Iteration No.:'.ljust(CST.LOG_NAME_WIDTH)}{self.n_iter}\n"
            f"  - {'Cuts No.:'.ljust(CST.LOG_NAME_WIDTH)}{self.n_opt_cuts + self.n_feas_cuts}"
            f" [Optimality: {self.n_opt_cuts}, Feasibility: {self.n_feas_cuts}]\n"
            f"  - {'Solve Time (sec.):'.ljust(CST.LOG_NAME_WIDTH)}{self.runtime:.4f}"
            f" [Master: {self.runtime_master:.4f}, Sub: {self.runtime_sub:.4f}]"
        )
        return summary

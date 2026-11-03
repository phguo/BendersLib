<div align="center">

![BendersLib Logo](https://raw.githubusercontent.com/phguo/BendersLib/397a53a490f2bbee0cccb3af39d4ee4e9d567301/docs/source/_static/benderslib.png)

[![GitHub Commits](https://img.shields.io/github/last-commit/phguo/benderslib?style=flat-square&logo=github)](https://github.com/phguo/BendersLib)
[![Codecov](https://img.shields.io/codecov/c/github/phguo/benderslib?style=flat-square&logo=codecov)](https://codecov.io/gh/phguo/BendersLib)
[![Pepy Downloads](https://img.shields.io/pepy/dt/benderslib?style=flat-square)](https://pepy.tech/projects/benderslib)
[![PyPI](https://img.shields.io/pypi/v/benderslib.svg?style=flat-square&logo=pypi)](https://pypi.org/project/benderslib/)
[![Python Versions](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fphguo%2FBendersLib%2Frefs%2Fheads%2Fdevelop%2Fpyproject.toml&style=flat-square&logo=python)](https://www.python.org/downloads/)
[![Read the Docs](https://img.shields.io/readthedocs/benderslib?style=flat-square&logo=readthedocs)](https://benders.dev)

</div>

---

# BendersLib: A Benders Decomposition Library in Python

**BendersLib** (https://benders.dev) is a Python library that supports a range of Benders decomposition
variants, including 
[Classical Benders Decomposition](https://benders.dev/tutorials/classical.html),
[Combinatorial Benders Decomposition](https://benders.dev/tutorials/cbd.html),
[Generalized Benders Decomposition](https://benders.dev/tutorials/gbd.html),
[L-shaped Method](https://benders.dev/tutorials/lshaped.html),
[Integer L-shaped Method](https://benders.dev/tutorials/ilshaped.html),
and [Logic-based Benders Decomposition](https://benders.dev/tutorials/lbbd.html).

While BendersLib provides built-in implementations of 
these methods, it is designed to be extensible. Users can implement custom Benders 
decomposition methods by customizing [subproblem solvers](https://benders.dev/manual/sub.html#customization) and [cut generators](https://benders.dev/manual/cuts.html#customization),
and defining [callback functions](https://benders.dev/manual/callbacks.html) for [enhancement strategies](https://benders.dev/tutorials/enhance.html).

BendersLib is solver 
agnostic and has built-in interfaces for popular Mathematical Programming and Constraint 
Programming [solvers](https://benders.dev/manual/solvers.html). Its support for rapid prototyping and high extensibility are designed
to meet the needs of both researchers and practitioners in Operations Research and related fields.

See the [documentation](https://benders.dev) for
[tutorials](https://benders.dev/tutorials), 
[manual](https://benders.dev/manual), 
[API reference](https://benders.dev/api), 
and [examples](https://benders.dev/examples).

## Quick Start

Install BendersLib and a solver of your choice (e.g., Gurobi) using pip.

```bash
python --version
# Should be Python 3.10 or higher

pip install "benderslib[gurobi]"

python -c "import benderslib as bd; print(bd.__url__)"
# Should output "https://benders.dev"
```

BendersLib enables switching from a standard Mathematical Programming model
to Benders decomposition with only a few lines of code.

```python
from benderslib import AnnotatedBenders, ClassicalBenders
from benderslib.solvers import Gurobi

from gurobipy import Model, GRB

# Create a standard Gurobi model
model = Model()
x = model.addVar(name="x", vtype=GRB.INTEGER)
y = model.addVar(name="y", vtype=GRB.CONTINUOUS)
model.addConstr(x + y >= 15)
model.addConstr(2 * x + 5 * y >= 30)
model.setObjective(3 * x + 4 * y)
model.update()

# Complicating variable
complicating_vars = ["x"]

# Create and solve using Benders decomposition
benders = AnnotatedBenders(
    model,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)
benders.solve()
print(f"Objective: {benders.result.obj}")
print(f"Solution: {benders.result.solution}")
```

The output will be similar to the following, showing the Benders decomposition process and results.

```
====================================================================================
BendersLib (v0.5.1, Apache-2.0, https://benders.dev) (C) 2021-2026 Peng-Hui Guo
------------------------------------------------------------------------------------
Benders Decomposition:
 - Method:                  ClassicalBenders
 - Complicating Var. No.:   1 [Integer: 1, Binary: 0, Continuous: 0]
 - Optimality Cut:          ClassicalOCGen
 - Feasibility Cut:         ClassicalFCGen
Master Problem:
 - Variable No.:            2 [Integer: 1, Binary: 0]
 - Constraint No.:          0
 - Solver:                  Gurobi
Sub Problem:
 - Variable No.:            1 [Integer: 0, Binary: 0]
 - Constraint No.:          2
 - Solver:                  Gurobi
Benders Parameters:
 - All default
------------------------------------------------------------------------------------
       Iter.,           LB,           UB,         Obj.,       Gap(%),   Runtime(s)
------------------------------------------------------------------------------------
           1,         0.00,        60.00,        60.00,       100.00,         0.00
------------------------------------------------------------------------------------
Benders Result:
  - Status:                  OPTIMAL
  - Incumbent:               45.0000
  - Bound:                   45.0000
  - Gap (abs.):              0.0000
  - Gap (rel.):              0.00%
  - Solutions No.:           2
  - Iteration No.:           2
  - Cuts No.:                1 [Optimality: 1, Feasibility: 0]
  - Solve Time (sec.):       0.01 [Master: 0.01, Sub: 0.00]
====================================================================================
Objective: 45.0
Solution: {'x': 15.0, 'y': 0.0}
```

More examples are available at https://benders.dev/examples.

## License

BendersLib's source code is licensed under the [Apache-2.0 License](https://github.com/phguo/BendersLib/blob/develop/LICENSE).

## References

- Benders, J. F. (1962). Partitioning procedures for solving mixed-variables programming problems. Numerische Mathematik, 4(1), 238–252. https://doi.org/10.1007/BF01386316
- Codato, G., & Fischetti, M. (2006). Combinatorial Benders’ cuts for mixed-integer linear programming. Operations Research, 54(4), 756–766. https://doi.org/10.1287/opre.1060.0286
- Geoffrion, A. M. (1972). Generalized Benders Decomposition. Journal of Optimization Theory and Applications, 10(4), 237–260. https://doi.org/10.1007/BF00934810
- Van Slyke, R. M., & Wets, R. (1969). L-shaped linear programs with applications to optimal control and stochastic programming. SIAM Journal on Applied Mathematics, 17(4), 638–663. https://doi.org/10.1137/0117061
- Laporte, G., & Louveaux, F. V. (1993). The integer L-shaped method for stochastic integer programs with complete recourse. Operations Research Letters, 13(3), 133–142. https://doi.org/10.1016/0167-6377(93)90002-X
- Hooker, J. N., & Ottosson, G. (2003). Logic-based Benders Decomposition. Mathematical Programming, 96(1), 33–60. https://doi.org/10.1007/s10107-003-0375-9

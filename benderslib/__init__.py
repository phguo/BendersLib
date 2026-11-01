# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

__version__ = "0.5.1"
__author__ = "Peng-Hui Guo"
__email__ = "m@guo.ph"
__license__ = "Apache-2.0"
__url__ = "https://benders.dev"
__copyright__ = "2021-2026 Peng-Hui Guo"

from .consts import BendersConsts
from .consts import BendersConsts as CST
from .params import BendersParams
from .result import BendersResult

from .solvers import SolverBase, SolverCPBase

from .core import (
    ProblemBase,
    MasterProblem,
    SubProblem,
    LogicBasedSubProblem,
    SubProblems,
    Cut,
    OptimalityCut,
    FeasibilityCut,
    CutGenerator,
    Oracle,
    BendersSolver
)

from .cuts import (
    # Cut types
    ClassicalOC,
    ClassicalFC,
    NoGoodFC,
    CombinatorialOC,
    LShapedOC,
    GeneralizedOC,
    GeneralizedFC,
    GeneLShapedOC,

    # Cut generators
    ClassicalFCGen,
    ClassicalOCGen,
    CombinatorialFCGen,
    CombinatorialOCGen,
    LShapedOCGen,
    LShapedFCGen,
    IntegerLShapedOCGen,
    IntegerLShapedFCGen,
    GeneralizedOCGen,
    GeneralizedFCGen,
    GeneLShapedOCGen
)

from .benders import (
    AnnotatedBenders,
    ClassicalBenders,
    CombinatorialBenders,
    LShaped,
    IntegerLShaped,
    LogicBasedBenders,
    GeneralizedBenders,
    GeneLShaped,
    OracleBenders
)

from .callback import (
    BendersContext,
    CallbackBase,
)

__all__ = [
    # Data
    "BendersConsts",
    "CST",
    "BendersParams",
    "BendersResult",

    # Solver
    "SolverBase",
    "SolverCPBase",

    # Core
    "ProblemBase",
    "MasterProblem",
    "SubProblem",
    "LogicBasedSubProblem",
    "SubProblems",
    "Cut",
    "OptimalityCut",
    "FeasibilityCut",
    "CutGenerator",
    "Oracle",
    "BendersSolver",

    # Cut types
    "ClassicalOC",
    "ClassicalFC",
    "NoGoodFC",
    "CombinatorialOC",
    "LShapedOC",
    "GeneralizedOC",
    "GeneralizedFC",
    "GeneLShapedOC",

    # Cut generators
    "ClassicalFCGen",
    "ClassicalOCGen",
    "CombinatorialFCGen",
    "CombinatorialOCGen",
    "LShapedOCGen",
    "LShapedFCGen",
    "IntegerLShapedOCGen",
    "IntegerLShapedFCGen",
    "GeneralizedOCGen",
    "GeneralizedFCGen",
    "GeneLShapedOCGen",

    # Benders methods
    "AnnotatedBenders",
    "ClassicalBenders",
    "CombinatorialBenders",
    "LShaped",
    "IntegerLShaped",
    "LogicBasedBenders",
    "GeneralizedBenders",
    "GeneLShaped",
    "OracleBenders",

    # Callbacks
    "BendersContext",
    "CallbackBase",
]

# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from typing import Type

from ..solvers import SolverBase
from ..core import BendersParams, MasterProblem, SubProblem, BendersSolver


class AnnotatedBenders(BendersSolver):
    """The class to perform Benders decomposition using annotation-based approach.

    This class decomposes the original problem into a master problem and a subproblem
    based on the specified complicating/master variables, and then applies the chosen Benders
    decomposition method to solve the problem.

    .. admonition:: Master problem variables vs. complicating variables
        :class: note

        The **master problem variables** are variables that appears only in the master problem.
        It has a subset, **complicating variables**, which are variables that are passed to the subproblem
        as known parameters.
        Though they are *sometimes identical*, the decomposition is based on the former.

    Parameters
    ----------
    original_problem:
        The original optimization problem in a solver-specific format.
    solver: Type[SolverBase]
        The solver class to be used for solving the master and subproblems, e.g., :class:`~.solvers.Gurobi`.
        It should be compatible with the :attr:`original_problem`.
    complicating_vars: list[str]
        A list of variable names that are considered complicating variables for the decomposition.
        The complicating variables are those that are passed to the subproblem as known parameters.
    master_vars: list[str], optional
        A list of variable names to be included in the master problem.
        The master variables are used to define the master problem and subproblem from the original problem.
        It is usually a superset of ``complicating_vars``.
        If not provided, it defaults to ``complicating_vars``.
    benders: Type[BendersSolver], optional
        The Benders decomposition method to be applied, e.g., :class:`ClassicalBenders`.
        If not provided, the class :class:`BendersSolver` will be used with the optimality
        and feasibility cut generators provided.
        If provided, parameters ``optimality_cut`` and ``feasibility_cut`` will be ignored,
        and the default cut generators of the chosen Benders method will be used.
    optimality_cut: Type[CutGenerator], optional
        The optimality cut generator to be used in the Benders decomposition.
        If not provided, the default optimality cut generator of the chosen Benders method ``benders`` will be used.
    feasibility_cut: Type[CutGenerator], optional
        The feasibility cut generator to be used in the Benders decomposition.
        If not provided, the default feasibility cut generator of the chosen Benders method ``benders`` will be used.
    params: BendersParams, optional
        An instance of :class:`BendersParams` containing parameters for the Benders decomposition process.
        If not provided, default parameters will be used.

    Caution
    -------
    - The ``solver`` should be a **class** (not an instance) that inherits from :class:`SolverBase`.
    - The ``benders`` should be a **class** (not an instance) that inherits from :class:`BendersSolver`.
    - The ``optimality_cut`` and ``feasibility_cut``, if provided, should be **classes** (not instances)
      that inherit from :class:`CutGenerator`.

    Example
    -------
    .. code-block:: python

        from benderslib import AnnotatedBenders, ClassicalBenders
        from benderslib.solvers import Gurobi

        original_problem = ...  # Define or load your original problem here
        complicating_vars = [...]  # List of complicating variable names
        master_vars = [...]  # List of master variable names (usually a superset of complicating_vars)

        BD = AnnotatedBenders(
            original_problem=original_problem,
            solver=Gurobi,
            benders=ClassicalBenders,
            complicating_vars=complicating_vars,
            master_vars=master_vars
        )
    """

    def __new__(
            cls,
            original_problem,
            solver: Type[SolverBase],
            complicating_vars: list[str],
            master_vars: list[str] = None,
            benders: Type[BendersSolver] = None,
            optimality_cut=None,
            feasibility_cut=None,
            params: BendersParams | None = None,
    ):
        master_vars = master_vars if master_vars is not None else complicating_vars
        master_problem, sub_problem = cls.decompose(original_problem, solver, master_vars)

        benders_kwargs = {
            "master_problem": master_problem,
            "sub_problem": sub_problem,
            "complicating_vars": complicating_vars,
            "params": params
        }

        if benders is None:
            benders = BendersSolver

        if optimality_cut is not None:
            benders_kwargs["optimality_cut"] = optimality_cut

        if feasibility_cut is not None:
            benders_kwargs["feasibility_cut"] = feasibility_cut

        return benders(**benders_kwargs)

    def __init__(self, *args, **kwargs):
        # This is intentionally left empty. The actual initialization is handled by the __new__ method,
        # which returns an instance of a different class (the one specified by the `benders` parameter).
        # By having AnnotatedBenders inherit from BendersSolver, documentation tools can correctly
        # identify and list the available methods.
        pass

    @staticmethod
    def decompose(
            original_problem,
            solver: Type[SolverBase],
            master_vars: list[str],
            solver_model=False
    ) -> tuple:
        """Decomposes the original problem into a master problem and a subproblem.

        It conducts automatic decomposition based on the given master variable names,
        using the methods :meth:`~benderslib.SolverBase.make_master_problem` and
        :meth:`~benderslib.SolverBase.make_sub_problem` provided by the solver interfaces.
        The original objective constant is retained only in the master problem.

        .. admonition:: Master problem variables vs. complicating variables
            :class: note

            The **master problem variables** are variables that appears only in the master problem.
            It has a subset, **complicating variables**, which are variables that are passed to the subproblem
            as known parameters.
            Though they are *sometimes identical*, the decomposition is based on the former.

        Parameters
        ----------
        original_problem:
            The original optimization problem in a solver-specific format.
        solver: Type[SolverBase]
            The solver class to be used for solving the master and subproblems.
        master_vars: list[str]
            A list of variable names to be included in the master problem.
        solver_model: bool, optional
            If ``True``, return the master and subproblem in the solver-specific format;
            If ``False``, return instances of :class:`MasterProblem` and :class:`SubProblem`.

        Returns
        -------
        tuple[MasterProblem, SubProblem] | tuple[object, object]
            A tuple containing the master problem and subproblem instances.

        Example
        --------
        .. code-block:: python

            from benderslib import AnnotatedBenders
            from benderslib.solvers import Gurobi

            original_problem = ...  # Define or load your original problem here
            master_vars = [...]  # List of master variable names (usually a superset of complicating_vars)

            master, sub = AnnotatedBenders.decompose(
                original_problem=original_problem,
                solver=Gurobi,
                master_vars=master_vars,
                solver_model=False  # (Default) Returns MasterProblem and SubProblem instances
            )
        """
        master = solver.make_master_problem(original_problem, master_vars)
        sub = solver.make_sub_problem(original_problem, master_vars)

        if solver_model:
            return master, sub
        else:
            return MasterProblem(solver(master)), SubProblem(solver(sub))

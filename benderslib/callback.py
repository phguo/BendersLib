# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from abc import ABC
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Type

from .consts import BendersConsts as CST
from .errors import BendersCallbackError

# Avoid circular imports
if TYPE_CHECKING:
    from .core import BendersResult, MasterProblem, SubProblem, BendersSolver, Cut


@dataclass
class BendersContext:
    """Context information passed to Benders decomposition callbacks.

    This dataclass bundles the objects that callbacks commonly need while
    observing or interacting with a running Benders decomposition. It is
    passed as the sole argument to all callback methods in :class:`CallbackBase`.
    """

    benders: "BendersSolver"
    """The Benders decomposition solver instance (:class:`BendersSolver`)."""
    master_problem: "MasterProblem"
    """The current master problem instance (:class:`MasterProblem`)."""
    sub_problem: "SubProblem"
    """The current subproblem instance (:class:`SubProblem`, :class:`SubProblems`, :class:`LogicBasedSubProblem`)."""
    state: "BendersResult"
    """The current state of the Benders decomposition process (:class:`BendersResult`)."""
    current_comp_vals: dict[str, float] = field(default_factory=dict)
    """A dictionary mapping complicating variable names to their current values in the master problem solution."""
    current_opti_cuts: list["Cut"] = field(default_factory=list)
    """A List of optimality cuts generated in the current iteration (:class:`OptimalityCut`)."""
    current_feas_cuts: list["Cut"] = field(default_factory=list)
    """A List of feasibility cuts generated in the current iteration (:class:`FeasibilityCut`)."""
    where: str = ""
    """An identifier for the Branch-and-check callback trigger location (:attr:`~benderslib.BendersConsts.INCUMBENT` or :attr:`~benderslib.BendersConsts.NODE`).
    
    This attributes is only relevant for callbacks in the Branch-and-check method.
    By default, the Branch-and-check callbacks are triggered when an incumbent solution
    is found. One can set :attr:`~benderslib.BendersParams.bnc_frac_sol` to ``True`` 
    to trigger callbacks at fractional solutions as well, in which case this attribute 
    will be set to :attr:`~benderslib.BendersConsts.NODE` for those triggers.
    
    Example
    ---------------
    
    .. code-block:: python
    
        def on_opti_cut_generated(self, context: BendersContext):
            if context.where == CST.INCUMBENT:
                print("Optimality cut generated at an incumbent solution!")
            if context.where == CST.NODE:
                print("Optimality cut generated at a fractional solution!")
        
        BD = BendersSolver(...)
        BD.params.bnc_frac_sol = True
        BD.register(on_opti_cut_generated)
        BD.bnc_solve()
    """

    def __str__(self):
        master_str = str(self.master_problem).replace('\n', '\n' + ' ' * 4)
        sub_str = str(self.sub_problem).replace('\n', '\n' + ' ' * 4)
        state_str = str(self.state).replace('\n', '\n' + ' ' * 4)
        return (f"{self.__class__.__name__}(\n"
                f"    master_problem={master_str},\n"
                f"    sub_problem={sub_str},\n"
                f"    state={state_str}\n"
                f")")


class CallbackBase(ABC):
    """Abstract base class for Benders decomposition callbacks.

    Users can define custom callbacks by inheriting from :class:`CallbackBase` and
    overriding the desired event methods. Each method receives a
    :class:`BendersContext` object containing information about the current
    state of the Benders decomposition process.
    Alternatively, users can define standalone functions with names matching
    the methods in :class:`CallbackBase` to serve as lightweight callbacks.

    A callbacks are passed to Benders decomposition instances via :meth:`~BendersSolver.register`.
    The callback can terminate the Benders process prematurely by returning
    the constant :attr:`~BendersConsts.TERMINATE`;
    If a callback returns :attr:`~BendersConsts.PROCEED` or does not return anything,
    the Benders process continues as normal.

    .. seealso::

        - See :ref:`callbacks-timeline` for the precise timeline of when each callback is triggered.
        - See :doc:`Examples (tag: callback) <../_tags/callback>` for callback usage examples.

    Example
    ---------------

    .. code-block:: python

        from benderslib import CallbackBase, BendersContext

        # Class-based callback
        class MyCallback(CallbackBase):

            def on_benders_start(self, context: BendersContext):
                print("Benders process started!")

        # Function-based callback
        def on_benders_end(self, context: BendersContext):
            print("Benders process finished!")

        BD = BendersSolver(...)
        BD.register(MyCallback())
        BD.register(on_benders_end)
    """

    def on_benders_start(self, context: BendersContext):
        """Called at the start of the Benders decomposition process.

        See :ref:`callbacks-timeline` for the precise timeline.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.

        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_benders_end(self, context: BendersContext):
        """Called at the end of the Benders decomposition process.

        See :ref:`callbacks-timeline` for the precise timeline.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.

        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_iteration_start(self, context: BendersContext):
        """Called at the start of each Benders decomposition iteration.

        See :ref:`callbacks-timeline` for the precise timeline.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.


        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_iteration_end(self, context: BendersContext):
        """Called at the end of each Benders decomposition iteration.

        See :ref:`callbacks-timeline` for the precise timeline.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.


        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_master_build(self, context: BendersContext):
        """Called after the master problem is built.

        See :ref:`callbacks-timeline` for the precise timeline.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.


        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_sub_build(self, context: BendersContext):
        """Called after the subproblem is built.

        See :ref:`callbacks-timeline` for the precise timeline.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.


        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_before_master_solve(self, context: BendersContext):
        """Called before solving the master problem.

        See :ref:`callbacks-timeline` for the precise timeline.

        .. caution::

           Not supported in the Branch-and-check method.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.


        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_after_master_solve(self, context: BendersContext):
        """Called after solving the master problem.

        See :ref:`callbacks-timeline` for the precise timeline.

        .. caution::

           Not supported in the Branch-and-check method.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.


        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_before_sub_solve(self, context: BendersContext):
        """Called before solving the subproblem.

        See :ref:`callbacks-timeline` for the precise timeline.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.


        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_after_sub_solve(self, context: BendersContext):
        """Called after solving the subproblem.

        See :ref:`callbacks-timeline` for the precise timeline.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.


        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_opti_cut_generated(self, context: BendersContext):
        """Called when an optimality cut is generated.

        See :ref:`callbacks-timeline` for the precise timeline.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.


        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_feas_cut_generated(self, context: BendersContext):
        """Called when a feasibility cut is generated.

        See :ref:`callbacks-timeline` for the precise timeline.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.


        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_opti_cut_added(self, context: BendersContext):
        """Called when an optimality cut is added to the master problem.

        See :ref:`callbacks-timeline` for the precise timeline.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.


        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_feas_cut_added(self, context: BendersContext):
        """Called when a feasibility cut is added to the master problem.

        See :ref:`callbacks-timeline` for the precise timeline.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.


        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_new_lower_bound(self, context: BendersContext):
        """Called when a higher lower bound is found.

        See :ref:`callbacks-timeline` for the precise timeline.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.


        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...

    def on_new_upper_bound(self, context: BendersContext):
        """Called when a lower upper bound is found.

        See :ref:`callbacks-timeline` for the precise timeline.

        Parameters
        ---------------

        context: :class:`BendersContext`
            The context object containing information about the current state of the Benders decomposition process.


        Returns
        ---------------

        :attr:`~benderslib.BendersConsts.TERMINATE`
            If the callback determines that the Benders process should be terminated immediately.
        :attr:`~benderslib.BendersConsts.PROCEED` or ``None``
            If the callback determines that the Benders process should continue as normal.
        """
        ...


class _CallbackEvents:
    """Enumeration of callback event names.

    The event names correspond to the method names in :class:`CallbackBase`,
    but are represented as uppercase strings.
    """

    ON_BENDERS_START = "ON_BENDERS_START"
    """See :meth:`CallbackBase.on_benders_start`."""
    ON_BENDERS_END = "ON_BENDERS_END"
    """See :meth:`CallbackBase.on_benders_end`."""
    ON_ITERATION_START = "ON_ITERATION_START"
    """See :meth:`CallbackBase.on_iteration_start`."""
    ON_ITERATION_END = "ON_ITERATION_END"
    """See :meth:`CallbackBase.on_iteration_end`."""
    ON_MASTER_BUILD = "ON_MASTER_BUILD"
    """See :meth:`CallbackBase.on_master_build`."""
    ON_SUB_BUILD = "ON_SUB_BUILD"
    """See :meth:`CallbackBase.on_sub_build`."""
    ON_BEFORE_MASTER_SOLVE = "ON_BEFORE_MASTER_SOLVE"
    """See :meth:`CallbackBase.on_before_master_solve`."""
    ON_AFTER_MASTER_SOLVE = "ON_AFTER_MASTER_SOLVE"
    """See :meth:`CallbackBase.on_after_master_solve`."""
    ON_BEFORE_SUB_SOLVE = "ON_BEFORE_SUB_SOLVE"
    """See :meth:`CallbackBase.on_before_sub_solve`."""
    ON_AFTER_SUB_SOLVE = "ON_AFTER_SUB_SOLVE"
    """See :meth:`CallbackBase.on_after_sub_solve`."""
    ON_OPTI_CUT_GENERATED = "ON_OPTI_CUT_GENERATED"
    """See :meth:`CallbackBase.on_opti_cut_generated`."""
    ON_FEAS_CUT_GENERATED = "ON_FEAS_CUT_GENERATED"
    """See :meth:`CallbackBase.on_feas_cut_generated`."""
    ON_OPTI_CUT_ADDED = "ON_OPTI_CUT_ADDED"
    """See :meth:`CallbackBase.on_opti_cut_added`."""
    ON_FEAS_CUT_ADDED = "ON_FEAS_CUT_ADDED"
    """See :meth:`CallbackBase.on_feas_cut_added`."""
    ON_NEW_LOWER_BOUND = "ON_NEW_LOWER_BOUND"
    """See :meth:`CallbackBase.on_new_lower_bound`."""
    ON_NEW_UPPER_BOUND = "ON_NEW_UPPER_BOUND"
    """See :meth:`CallbackBase.on_new_upper_bound`."""


class _CallbackManager:
    """Manager for handling multiple Benders decomposition callbacks.

    This class is initialized within :class:`BendersSolver` and is responsible for
    registering and triggering callbacks at appropriate events during the Benders
    decomposition process.
    """

    def __init__(self):
        self.callbacks: list[CallbackBase] = []

    def register(self, callback: CallbackBase | Callable | Type[CallbackBase]):
        if isinstance(callback, type) and issubclass(callback, CallbackBase):
            # Handle class-based callbacks by instantiating them
            callback = callback()

        if not isinstance(callback, CallbackBase):
            # Handle functions as callbacks
            callback = _FuncWrapperCallback(callback)

        self.callbacks.append(callback)

    def trigger(self, event: str, context: BendersContext):
        for callback in self.callbacks:
            context.where = context.master_problem._callback_where
            event = event.lower()
            method = getattr(callback, event, None)

            if callable(method):
                action = method(context)

                if action == CST.TERMINATE:
                    return CST.TERMINATE
        return CST.PROCEED


class _FuncWrapperCallback(CallbackBase):
    """A wrapper class to allow using functions as callbacks."""

    valid_events = [
        func for func in dir(CallbackBase)
        if callable(getattr(CallbackBase, func))
           and not func.startswith("__")
    ]

    def __init__(self, func):
        self._func = func

        if self._func.__name__ not in self.valid_events:
            raise BendersCallbackError(f"Function name '{self._func.__name__}' should be one of: {self.valid_events}")

        if hasattr(self._func, '__name__'):
            setattr(self, self._func.__name__, self._func)

Callbacks
====================================

.. currentmodule:: benderslib

What are Callbacks?
------------------------------------

This section provides an overview of the `callback <https://en.wikipedia.org/wiki/Callback_(computer_programming)>`_
system in BendersLib.
Callbacks are functions executed at specific events during the Benders decomposition,
allowing for monitoring and intervention.

The primary motivation for callbacks in BendersLib is to allow users to "hook into" the algorithm,
making it a flexible and extensible framework.
By providing hooks into the solver's lifecycle, callbacks enable monitoring progress,
extracting intermediate data, or customizing behavior without altering the core library.
They are the primary mechanism for extending the Benders decomposition with advanced strategies
like custom cut generation, problem-specific heuristics, and other acceleration techniques,
which can significantly improve performance, stability, and convergence.
See :doc:`../tutorials/enhance` for advanced acceleration techniques supported by BendersLib.

The callback system in BendersLib operates on an event-driven basis.
The :class:`BendersSolver` emits events at various stages of the decomposition process.
When an event is emitted, the solver checks for any registered callbacks corresponding
to that event and executes them sequentially.
A callback can also terminate the Benders process prematurely by returning the constant :attr:`~BendersConsts.TERMINATE`;
If a callback returns :attr:`~BendersConsts.PROCEED` or does not return anything, the Benders process continues as normal.
Any :attr:`~BendersConsts.TERMINATE` signal is executed immediately after the current event completes,
meaning that the subsequent steps in the current iteration will not be executed,
with the :attr:`~BendersResult.status` of the Benders process set to :attr:`~BendersConsts.TERMINATED`.

.. _callbacks-timeline:

.. rubric:: Timeline of Callback Triggers

The following pseudocode (:func:`~BendersSolver.solve`) illustrates the main stages of the
Benders decomposition algorithm and the specific points at which each callback event is triggered.

.. parsed-literal::

    // solve() method of BendersSolver is called

    trigger :meth:`~CallbackBase.on_master_build`
    trigger :meth:`~CallbackBase.on_sub_build`
    trigger :meth:`~CallbackBase.on_benders_start`

    iteration counter = 0

    while not converged:
        increment iteration counter
        trigger :meth:`~CallbackBase.on_iteration_start`

        trigger :meth:`~CallbackBase.on_before_master_solve`
        **solve master problem**
        trigger :meth:`~CallbackBase.on_after_master_solve`

        if master problem is optimal:
            save :attr:`~BendersContext.current_comp_vals`
            trigger :meth:`~CallbackBase.on_before_sub_solve`
            **solve subproblem with** :attr:`~BendersContext.current_comp_vals`
            trigger :meth:`~CallbackBase.on_after_sub_solve`

            if subproblem is optimal:
                if new lower bound is found:
                    trigger :meth:`~CallbackBase.on_new_lower_bound`
                if new upper bound is found:
                    // new best-known solution found
                    trigger :meth:`~CallbackBase.on_new_upper_bound`

                if converged:
                    break

                **generate optimality cut**
                save :attr:`~BendersContext.current_opti_cuts`
                trigger :meth:`~CallbackBase.on_opti_cut_generated`
                add :attr:`~BendersContext.current_opti_cuts` to master problem
                trigger :meth:`~CallbackBase.on_opti_cut_added`

            else if subproblem is infeasible:
                if converged:
                    break

                **generate feasibility cut**
                save :attr:`~BendersContext.current_feas_cuts`
                trigger :meth:`~CallbackBase.on_feas_cut_generated`
                add :attr:`~BendersContext.current_feas_cuts` cut to master problem
                trigger :meth:`~CallbackBase.on_feas_cut_added`

        else:
            // master problem is infeasible or unbounded
            break

        trigger :meth:`~CallbackBase.on_iteration_end`

    trigger :meth:`~CallbackBase.on_benders_end`

.. _branch-and-check-timeline:

.. rubric:: Timeline of Branch-and-check Callback Triggers

The following pseudocode (:func:`~BendersSolver.bnc_solve`) illustrates the main stages of the
:ref:`branch-and-check method <enhance_branch_and_check>` and the specific points at which
each callback event is triggered.
Note that the callback events :meth:`~CallbackBase.on_before_master_solve` and
:meth:`~CallbackBase.on_after_master_solve` are not triggered in the Branch-and-check method.

.. parsed-literal::

    // bnc_solve() method of BendersSolver is called

    trigger :meth:`~CallbackBase.on_master_build`
    trigger :meth:`~CallbackBase.on_sub_build`
    trigger :meth:`~CallbackBase.on_benders_start`

    // Master problem is solved using a MIP solver with a callback
    // The following events are triggered within the solver's callback at each node

    if node is integer and feasible:
        trigger :meth:`~CallbackBase.on_iteration_start`
        save :attr:`~BendersContext.current_comp_vals`
        trigger :meth:`~CallbackBase.on_before_sub_solve`
        **solve subproblem with** :attr:`~BendersContext.current_comp_vals`
        trigger :meth:`~CallbackBase.on_after_sub_solve`

        if subproblem is optimal:
            if new lower bound is found:
                trigger :meth:`~CallbackBase.on_new_lower_bound`
            if new upper bound is found:
                // new best-known solution found
                trigger :meth:`~CallbackBase.on_new_upper_bound`

            **generate optimality cut**
            save :attr:`~BendersContext.current_opti_cuts`
            trigger :meth:`~CallbackBase.on_opti_cut_generated`
            add :attr:`~BendersContext.current_opti_cuts` to master problem at the current node
            trigger :meth:`~CallbackBase.on_opti_cut_added`

        else if subproblem is infeasible:
            **generate feasibility cut**
            save :attr:`~BendersContext.current_feas_cuts`
            trigger :meth:`~CallbackBase.on_feas_cut_generated`
            add :attr:`~BendersContext.current_feas_cuts` cut to master problem at the current node
            trigger :meth:`~CallbackBase.on_feas_cut_added`

        trigger :meth:`~CallbackBase.on_iteration_end`

    trigger :meth:`~CallbackBase.on_benders_end`


How to Use Callbacks?
------------------------------------

There are two ways to create callbacks: as a class inheriting from :class:`CallbackBase` or as a standalone function.
Both approaches receive a :class:`BendersContext` object, which provides access to the master problem, subproblem,
and the current state of the decomposition.
The **class-based** callbacks are ideal for complex logic that requires maintaining state between events.
By defining a class, you can use instance attributes to store information across different callback calls.
The **function-based** callbacks is a simpler, more direct way to respond to events when you don not  need to
maintain state. Each callback function is independent.

The following :doc:`example <../examples/expert/simple_callback>`
demonstrates how to define and register both types of callbacks.

.. code-block:: python
    :caption: Defining and registering callbacks in BendersLib

    # Class-based callback
    class MyCallback(CallbackBase):
        some_persistent_data = ">>>>>>>> Hi there! >>>>>>>>>"

        def on_benders_start(self, context: BendersContext):
            print("Benders process started!")
            print(self.some_persistent_data)

    # Function-based callback
    def on_iteration_end(context: BendersContext):
        print(f"Starting iteration: {context.state.n_iter} ...")

        if context.state.n_iter == 1:
            print("Reached maximum iterations, terminating...")
            return CST.TERMINATE

    master_model, complicating_vars = make_master_problem()
    sub_model = make_sub_problem()

    benders = ClassicalBenders.from_models(
        master_model, Gurobi,
        sub_model, Gurobi,
        complicating_vars=complicating_vars
    )

    # Register the callback
    benders.register(MyCallback)
    benders.register(on_iteration_end)

    benders.solve()

.. admonition:: Example
    :class: seealso

    More callback examples can be found in the :doc:`Examples (tag: callback) <../_tags/callback>`.

Registering Multiple Callbacks
------------------------------------

BendersLib supports registering multiple callbacks for the same event.
When multiple callbacks are registered for a single event, they are
**executed sequentially in the order they were registered** in that event.
This allows for modular design, where different callbacks can
handle different aspects of the same event without interfering
with each other. For example, one callback could be responsible for
logging the progress of the algorithm, while another could be
responsible for implementing a custom stopping criterion.

.. warning::

    **Use caution when registering multiple callbacks**, especially
    for the same event, as they may interact unexpectedly, particularly
    if they modify the same attributes in the :class:`BendersContext`.

.. _manual_callback_attributes_methods:

Attributes & Methods
------------------------------------

The class :class:`CallbackBase` is the abstract base class for creating ``CustomCallback``.
It provides a set of methods that are triggered at specific events during the Benders decomposition process.
Each callback method has a :class:`BendersContext` object, which contains the attributes listed below,
providing access to the current state of the solver.
During the iterations, callbacks are triggered by :class:`BendersSolver` at the appropriate times.

.. mermaid::
    :caption: Callback System Inheritance Diagram
    :align: center

    flowchart LR
        BendersSolver -- triggers --> CustomCallback
        CustomCallback -- has --> BendersContext
        CustomCallback -- inherits --> CallbackBase

        style BendersSolver fill:#f2f2f2,stroke:#333,stroke-width:1px
        style CustomCallback fill:white,stroke:#333,stroke-width:1px

.. rubric:: :class:`BendersContext` - Attributes

.. autosummary::
   :nosignatures:

   ~BendersContext.benders
   ~BendersContext.master_problem
   ~BendersContext.sub_problem
   ~BendersContext.state
   ~BendersContext.current_comp_vals
   ~BendersContext.current_opti_cuts
   ~BendersContext.current_feas_cuts

.. rubric:: :class:`CallbackBase` - Methods

.. autosummary::
   :nosignatures:

   ~CallbackBase.on_benders_start
   ~CallbackBase.on_benders_end
   ~CallbackBase.on_iteration_start
   ~CallbackBase.on_iteration_end
   ~CallbackBase.on_master_build
   ~CallbackBase.on_before_master_solve
   ~CallbackBase.on_after_master_solve
   ~CallbackBase.on_sub_build
   ~CallbackBase.on_before_sub_solve
   ~CallbackBase.on_after_sub_solve
   ~CallbackBase.on_opti_cut_generated
   ~CallbackBase.on_feas_cut_generated
   ~CallbackBase.on_opti_cut_added
   ~CallbackBase.on_feas_cut_added
   ~CallbackBase.on_new_lower_bound
   ~CallbackBase.on_new_upper_bound

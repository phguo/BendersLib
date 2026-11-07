Quickstart
=====================================================

.. currentmodule:: benderslib

.. _suitable-problem:

Is Benders Decomposition suitable for your problem?
-----------------------------------------------------

   "*If an algorithm does particularly well on average for one class of problems then it must do worse on average over the remaining problems.*"

   -- The No Free Lunch (NFL) Theorem [#]_

Benders Decomposition is a powerful technique, but it's not a silver bullet.
It is designed for a specific class of optimization problems.
Before investing time in modeling your problem for this framework,
review this checklist to see if your problem is a good candidate.
Your problem is likely a good fit for Benders Decomposition if you can answer *yes* to most of the following questions.

* **Does your problem have a decomposable structure?**

  Benders Decomposition is designed for problems where variables can be split into two sets: complicating and subproblem variables.
  When the complicating variables are fixed to a specific value, the remaining problem should decompose into one
  or more independent and much simpler subproblems.
  A :ref:`block-diagonal structure <tutorials-lshaped-block>` connected by a few linking variables is a classic example of this.

* **Does the problem become easy after fixing the complicating variables?**

  The algorithm's performance depends on solving the subproblem(s) quickly.
  If the subproblem is itself time-consuming, the overall process will be slow.
  An ideal subproblem is one that can be solved very efficiently,
  such as Linear Programming, convex Quadratic Programming,
  or a problem with a special structure like a network flow problem.

* **Are there a small number of high-impact strategic decisions?**

  A good Benders model separates *strategic* from *operational* decisions.
  The complicating variables should represent the few, high-level strategic choices
  that are the primary source of combinatorial difficulty
  (e.g., "which facilities to build?", "which investments to make?").
  The vast number of remaining variables should represent the
  operational fallout from those choices (e.g., "how to route products?", "what is the return on the investment?").

* **Is your problem too large for a standard solver?**

  .. important::

     Use a standard solver before trying Benders Decomposition.

  Using a standard mathematical optimization solver for the full problem is often simpler when feasible.
  Benders decomposition is advantageous when a monolithic model becomes too large to solve directly,
  leading to out-of-memory errors or prohibitive runtimes.
  By breaking the problem down, Benders can find high-quality solutions using significantly less memory.

.. tip::

    Problems that can benefit from Benders Decomposition (not exhaustive):

    * **Facility Location**

      * ✅ Facility location problems decompose into facility opening decisions and customer assignment decisions.
      * ✅ The assignment decisions can typically be formulated with Linear Programming.
      * ✅ The facility opening decisions are strategic and few in number.
      * ✅ Large-scale facility location problems can be too big for standard solvers.

    * **Two-stage stochastic programming**

      * ✅ Two-stage stochastic programming problems are naturally decomposable by stage.
      * 🟨 When the recourse problem is Linear Programming, the subproblems can be solved efficiently.
      * ✅ The first-stage decisions are typically few and strategic, deciding before uncertainty is revealed.
      * ✅ Sample Average Approximation based deterministitc equivalent can be huge depending on the number of scenarios.

    * *To be added (after the application examples are completed)*

However, **exceptions exist**, and experimentation is often the best way to determine suitability.
BendersLib makes this easy.

Step-by-Step Guide
-----------------------------------------------------

The following steps take :doc:`../tutorials/classical` as an example to demonstrate how to use BendersLib
to model and solve an optimization problem.
Other variants of Benders Decomposition follow a similar workflow, please refer to :doc:`benders` for more details.

.. admonition:: Example
    :class: seealso

    The executable code is available at :doc:`../examples/basic/classical_benders`.

Step 1: Building the Master Problem
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Build a master problem using the API of an off-the-shelf solver :doc:`supported by BendersLib <solvers>`,
such as Gurobi.

.. code-block:: python

    from gurobipy import Model, GRB

    # Create a Gurobi model for the master problem
    master_model = Model("master_problem")

    # Define variables, objective, and constraints for the master problem
    x = master_model.addVars( ... )  # Add your variables here
    y = master_model.addVars( ... )  # Add your complicating variables here
    master_model.setObjective( ... , GRB.MINIMIZE)  # Set your objective here
    master_model.addConstrs( ... )  # Add your constraints here

    complicating_vars = [v.VarName for v in y.values()]  # List of complicating variable names

Wrap the solver model with BendersLib's :class:`~.solvers.Gurobi` interface and the :class:`MasterProblem` class.

.. code-block:: python

    from benderslib import MasterProblem
    from benderslib.solvers import Gurobi

    master_problem = MasterProblem(Gurobi(master_model))
    print(master_problem)

    # The output should look like:
    # Master Problem:
    #  - Variable No.:            2 [Integer: 1, Binary: 0]
    #  - Constraint No.:          0
    #  - Solver:                  Gurobi

Step 2: Building the Subproblem
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Build a subproblem using the API of an off-the-shelf solver :doc:`supported by BendersLib <solvers>`,
such as Gurobi.
The subproblem can use a different solver from the master problem.

.. code-block:: python

    from gurobipy import Model, GRB

    # Create a Gurobi model for the subproblem
    subproblem_model = Model("subproblem")

    # Define variables, objective, and constraints for the subproblem
    y = subproblem_model.addVars( ... )  # Add your complicating variables here
    z = subproblem_model.addVars( ... )  # Add your subproblem variables here
    subproblem_model.setObjective( ... , GRB.MINIMIZE)  # Set your objective here
    subproblem_model.addConstrs( ... )  # Add your constraints here

.. attention::

    The complicating variables defined in the master problem should also appear in the subproblem,
    with exactly the **same** names.
    Internally, BendersLib treats them as parameters in the subproblem by fixing their
    values to the values given by the master problem at each iteration.

Wrap the solver model with BendersLib's :class:`~.solvers.Gurobi` interface and the :class:`SubProblem` class.

.. code-block:: python

    from benderslib import SubProblem
    from benderslib.solvers import Gurobi

    subproblem = SubProblem(Gurobi(subproblem_model))
    print(subproblem)

    # The output should look like:
    # Sub Problem:
    #  - Variable No.:            1 [Integer: 0, Binary: 0]
    #  - Constraint No.:          2
    #  - Solver:                  Gurobi

Step 3: Building the Benders Decomposition Instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Build a Benders Decomposition instance using the :class:`ClassicalBenders` class,
by providing the master problem, subproblem, and the list of complicating variable names.

.. code-block:: python

    from benderslib import ClassicalBenders

    BD = ClassicalBenders(
        master_problem=master_problem,
        subproblem=subproblem,
        complicating_var_names=complicating_vars
    )
    print(BD)

    # The output should look like:
    # Benders Decomposition:
    #  - Method:                  ClassicalBenders
    #  - Complicating Var. No.:   2 [Integer: 1, Binary: 0, Continuous: 1]
    #  - Optimality Cut:          ClassicalOCGen
    #  - Feasibility Cut:         ClassicalFCGen

The output suggests that two bulti-in cut generators
(:class:`ClassicalOCGen` for *optimality cuts*, and :class:`ClassicalFCGen` for *feasibility cuts*)
are used for generating Benders cuts.

Step 4: Solving the Instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Solve the Benders Decomposition instance by simply using its :meth:`ClassicalBenders.solve` method.
Before calling this method, you can customize various parameters of the Benders algorithm
by modifying the attributes of the :attr:`ClassicalBenders.params` (a :class:`BendersParams` object).

.. code-block:: python

    BD.params.time_limit = 600  # Set a time limit of 600 seconds
    BD.solve()

Basic statistics are printed after the solve.

.. code-block:: text

    ====================================================================================
    BendersLib (v0.6.0, Apache-2.0, https://benders.dev) (C) 2021-2026 Peng-Hui Guo
    ------------------------------------------------------------------------------------
    Benders Decomposition:
     - Method:                  ClassicalBenders
     - Complicating Var. No.:   2 [Integer: 1, Binary: 0, Continuous: 1]
     - Optimality Cut:          ClassicalOCGen
     - Feasibility Cut:         ClassicalFCGen
    Master Problem:
     - Variable No.:            3 [Integer: 1, Binary: 0]
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
               3,         2.00,         2.00,         2.00,         0.00,         0.00
    ------------------------------------------------------------------------------------
    Benders Result:
      - Status:                  OPTIMAL
      - Incumbent:               2.0000
      - Bound:                   2.0000
      - Gap (abs.):              0.0000
      - Gap (rel.):              0.00%
      - Solutions No.:           1
      - Iteration No.:           3
      - Cuts No.:                2 [Optimality: 0, Feasibility: 2]
      - Solve Time (sec.):       0.00 [Master: 0.00, Sub: 0.00]
    ====================================================================================

A more detailed set of statistics is available via the :attr:`ClassicalBenders.result`
attributes (a :class:`BendersResult` object) of the Benders Decomposition instance.
A detailed description of the statistics is provided in :doc:`logging`.

.. seealso::

    BendersLib supports multiple variants of Benders Decomposition,
    including but not limited to the above classical approach, and allows for customization beyond the built-in options.
    Please refer to :doc:`benders` for more details on other variants and their usage.

Conventions
-----------------------------------------------------

BendersLib follows a set of conventions to ensure consistency and predictability.

*   **Variable Bounds**:
    BendersLib requires all decision variables to be **non-negative**.
    Internally, all variable bounds are transfromed into explicit linear constraints.
    Any lower bounds or upper bounds defined directly on a variable
    during model creation will be converted into standard constraints.
    This ensures that all boundary conditions are treated uniformly as
    part of the constraint matrix within the framework.

*   **Objective Sense**:
    BendersLib standardizes on **minimization** problems. Maximization problems are not
    supported and must be converted by the user. This is achieved by negating the
    objective function (e.g., transforming :math:`\max c^T x` to :math:`\min -c^T x`).

*   **Dual Values**:
    The dual values from a subproblem's constraints are used to generate *optimality cuts*.
    Their sign, however, can differ between solvers. This is because a constraint like
    :math:`A y \ge b` might have a non-negative dual in one solver, while another solver
    might internally use :math:`-A y \le -b` and report a dual with the opposite sign.
    Both values are mathematically correct, corresponding to equivalent dual formulations.
    BendersLib internally ensures consistent signs from all solver backends.

*   **Extreme Rays**:
    When a subproblem is infeasible, an *extreme ray* of its dual is used to generate a
    *feasibility cut*. Similar to duals, its sign can be inverted. An extreme ray ``v``
    defines a direction of unboundedness; if :math:`r` is a valid ray, so is :math:`-r` as they
    describe the same unbounded line. A solver may return either. Both are correct and produce equivalent cuts.
    BendersLib internally ensures consistent signs from all solver backends.

References
-----------------------------------------------------

.. [#] Wolpert, D. H., & Macready, W. G. (1997). No free lunch theorems for optimization. IEEE Transactions on Evolutionary Computation, 1(1), 67–82. https://doi.org/10.1109/4235.585893

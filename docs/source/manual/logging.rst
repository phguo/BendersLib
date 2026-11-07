Logging and Profiling
=====================================================

.. currentmodule:: benderslib

Understanding the Log
-----------------------------------------------------

Below is a typical output from a Benders decomposition run using BendersLib.
The output provides a comprehensive summary of the Benders decomposition process.
Here's a breakdown of what each section means.

.. code-block:: text

    ====================================================================================
    BendersLib (v0.6.0, Apache-2.0, https://benders.dev) (C) 2021-2026 Peng-Hui Guo
    ------------------------------------------------------------------------------------
    Benders Decomposition:
     - Method:                  ClassicalBenders
     - Complicating Var. No.:   20 [Integer: 0, Binary: 20]
     - Optimality Cut:          ClassicalOCGen
     - Feasibility Cut:         ClassicalFCGen
    Master Problem:
     - Variable No.:            20 [Integer: 0, Binary: 20]
     - Constraint No.:          40
     - Solver:                  Gurobi
    Sub Problem:
     - Variable No.:            20 [Integer: 0, Binary: 0]
     - Constraint No.:          101
     - Solver:                  Gurobi
    Benders Parameters:
     - All default
    ------------------------------------------------------------------------------------
           Iter.,           LB,           UB,         Obj.,       Gap(%),   Runtime(s)
    ------------------------------------------------------------------------------------
               1,         0.00,        73.50,        73.50,       100.00,         0.00
              42,        69.20,        73.40,        72.30,         4.22,         0.52
              62,        70.00,        75.70,        72.30,         3.04,         1.03
              80,        70.30,        75.40,        72.30,         2.65,         1.54
              97,        70.90,        76.60,        72.30,         1.83,         2.07
             111,        71.20,        75.40,        72.30,         1.46,         2.61
             122,        71.50,        75.10,        72.30,         1.07,         3.17
             133,        71.50,        75.70,        72.30,         1.06,         3.68
             147,        71.70,        72.60,        72.30,         0.83,         4.21
             162,        72.00,        75.60,        72.30,         0.40,         4.74
             174,        72.00,        74.70,        72.30,         0.40,         5.28
             185,        72.30,        76.20,        72.30,         0.00,         5.79
    ------------------------------------------------------------------------------------
    Benders Result:
      - Status:                  OPTIMAL
      - Incumbent:               72.3000
      - Bound:                   72.3000
      - Gap (abs.):              0.0000
      - Gap (rel.):              0.00%
      - Solutions No.:           185
      - Iteration No.:           185
      - Cuts No.:                184 [Optimality: 184, Feasibility: 0]
      - Solve Time (sec.):       5.79 [Master: 5.71, Sub: 0.02]
    ====================================================================================

The first block details the configuration of the Benders decomposition algorithm
and the characteristics of the master and subproblems.

- **Benders Decomposition**: This part specifies the core components of the Benders algorithm being used.
- **Master Problem**: This describes the scale of the master problem, including the number of variables and constraints,
  and the solver used.
- **Subproblem**: Similarly, this shows the size of the subproblem and its solver.
- **Benders Parameters**: This indicates if any default parameters (:class:`BendersParams`)
  of the Benders algorithm have been changed.

The second block provides a log of the algorithm's progress at different iterations.

- **Iter.**: The current iteration number.
- **LB (Lower Bound)**: The best lower bound found so far, which is obtained from the master problem.
  The lower bound is typically non-decreasing across iterations as more cuts are added to the master problem.
  However, certain techniques (e.g., trust region methods) may allow for temporary decreases in the lower bound.
- **UB (Upper Bound)**: The objective value of the integer feasible solution found in the current iteration.
  If no feasible solution is found in the current iteration, this will be the objective value of the integer
  feasible solution found in the latest previous iteration.
- **Obj.**: The objective value of the best integer feasible solution found (the incumbent).
- **Gap (%)**: The relative gap between the upper and lower bounds, calculated as ``|UB - LB| / |UB|``.
- **Runtime (s)**: The elapsed time in seconds.

The final block summarizes the outcome of the decomposition process.

- **Status**: Indicates whether the problem was solved to optimality (see :class:`BendersConsts` for possible values).
- **Incumbent**: The objective value of the best solution found.
- **Bound**: The final lower bound upon termination.
- **Gap**: The final absolute and relative gaps between the incumbent and the bound.
- **Solutions No.**: The total number of feasible solutions found during the process.
- **Iteration No.**: The total number of iterations performed.
- **Cuts No.**: The total number of optimality and feasibility cuts added to the master problem.
- **Solve Time (sec.)**: The total time taken to solve the problem, with a breakdown of the time
  spent in the master problem and the subproblems.

More statistics can be retrieved from the :class:`BendersResult` object via :attr:`BendersSolver.result`,
after the Benders decomposition process is complete.
Alternatively, you can also obtain real-time statistics during the Benders decomposition process
by implementing a custom :doc:`callback <callbacks>` function (:doc:`example <../examples/expert/save_solutions>`).

Profiling
-----------------------------------------------------

Benders decomposition can be accelerated by focusing on two main areas:
speeding up the solution of each iteration and reducing the total number of iterations.
The profiling statistics offered by BendersLib can help identify which of these areas to focus on.

- **Master Problem Time**:
  A long master problem solution time can be addressed by warm starting with the solution from the
  previous iteration or by periodically removing inactive cuts to reduce the problem size.
  Trust region methods and local branching can also help by limiting the search space.

- **Subproblem Time**:
  If the subproblems are a bottleneck, consider solving them in parallel, warm starting the solution process,
  or using a specialized solver (e.g., a CP solver for scheduling subproblems) that is better suited to the
  subproblem's structure.
  Long subproblem times can also be a sign of instability, which lead to enormous subproblems to be solved.

- **Number of Cuts**:
  A large number of cuts may indicate that the generated cuts are weak. Stronger cuts can be
  obtained by generating Pareto-optimal cuts, adding global valid inequalities, or using cut lifting techniques.

- **Number of Iterations**:
  A high number of iterations might point to slow convergence or instability. To improve this,
  you can normalize cuts for better numerical stability, use a trust region to limit solution
  changes between iterations, employ local branching to explore the solution neighborhood,
  or implement an early stopping criterion to terminate the algorithm if the objective improvement stagnates.

For a more detailed discussion of these and other enhancement strategies, please refer to
the :doc:`../tutorials/enhance` tutorial.

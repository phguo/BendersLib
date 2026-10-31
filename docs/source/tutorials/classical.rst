Classical Benders Decomposition
============================================

.. currentmodule:: benderslib

.. role:: raw-latex(raw)
   :format: latex

.. default-role:: raw-latex

Original Problem
---------------------------------

The Benders decomposition [#]_ is applied to MILPs or other problems that have a mix of "difficult" and "easy" variables.
The difficult variable, namely "**complicating variables**", are variables that, if their values were fixed,
would make the rest of the problem much easier to solve.
The canonical example is a problem with both integer variables and continuous variables.
Consider the following MILP

.. math::
   \begin{aligned}
   \min_{x, y} \quad & c^T x + f^T y \\
   \text{s.t.} \quad & Ax + By \geq b \\
                     & x \in X \\
                     & y \in Y
   \end{aligned}

where :math:`x \geq 0` are the complicating (e.g., integer) variables and :math:`y \geq 0` are the easy (continuous) variables.
The key insight is that if :math:`x` is fixed to a specific value :math:`\bar{x}`, the remaining problem in `y`
becomes a simple pure LP, which is easy to solve.
The Benders Decomposition method reformulates the problem into **master problem** and **subproblem** based on the
complicating and easy variables.
**Benders cuts** are then generated from the subproblem and added to the master problem to iteratively refine the solution.

Reformulation
------------------
The master problem works only with the complicating variables :math:`x`. 
Its goal is to find the best possible values for :math:`x` by considering the overall objective function. 
It approximates the impact of the :math:`y` variables using a single variable :math:`\eta`, 
which represents the optimal cost of the subproblem.
The **master problem** with iteratively added constraints, known as
**Benders cuts** (optimality cuts and feasibility cuts), is as follows.

.. math::
   \begin{aligned}
   \min_{x, \eta} \quad & c^T x + \eta \\
   \text{s.t.} \quad & x \in X \\
                     & \eta \geq \dots (\text{optimality cuts}) \\
                     & 0 \geq \dots (\text{feasibility cuts}) \\
                     & -\infty < \eta < +\infty
   \end{aligned}


Once the master problem proposes a candidate solution :math:`\bar{x}`,
the subproblem is solved to find the optimal values of :math:`y` for that fixed :math:`\bar{x}`.
The **primal subproblem** for a given :math:`\bar{x}` is as follows.

.. math::
   \begin{aligned}
   \min_{y} \quad & f^T y \\
   \text{s.t.} \quad & By \geq b - A \bar{x} \\
                     & y \in Y
   \end{aligned}

This is a pure LP. However, the information we need for the Benders cuts comes from its *dual*.
The **dual subproblem** is as follows.

.. math::
   \begin{aligned}
   \max_{\pi} \quad & \pi^T (b - A \bar{x}) \\
   \text{s.t.} \quad & B^T \pi \leq f \\
                     & \pi \geq 0
   \end{aligned}

Solving this dual subproblem has two possible outcomes that are crucial for the algorithm:

1.  **Finite optimal:** The dual problem has an optimal solution :math:`\bar{\pi}`.
    By strong duality, this means the primal subproblem is feasible and has an optimal solution.
    This outcome leads to a **Benders Optimality Cut**, formulated based on :math:`\bar{\pi}`.
2.  **Unbounded:** The dual problem is unbounded. By the weak duality theorem,
    this implies that the primal subproblem is infeasible.
    This outcome leads to a **Benders Feasibility Cut**, formulated based on an *extreme ray* of the dual feasible region.

.. tip::

    One do not need to explicitly formulate the dual subproblem,
    since modern LP solvers can provide the *dual values* (for optimality cuts)
    or *extreme rays* (for feasibility cuts) directly when solving the primal subproblem.

Benders Cuts
-----------------

Benders cuts are the constraints added back to the master problem to inform it about the consequences of choosing a particular `x`.

Optimality Cut
^^^^^^^^^^^^^^^^^

*   **When is it generated?** When the subproblem is feasible for a given :math:`\bar{x}`, yielding an optimal dual solution :math:`\bar{\pi}`.

*   **What is the logic?** The optimal cost of the subproblem for :math:`\bar{x}` is :math:`\bar{\pi}^T (b - A \bar{x})`.
    The master problem's variable :math:`\eta` must be at least this large. We can generalize this for any
    :math:`(x, \eta)` pair to create a valid cut that constrains :math:`\eta`.

*   **The Cut:** We add the following linear constraint to the master problem.

    .. math::
       \eta \geq \bar{\pi}^T (b - A x)

.. note::

    *   This cut tells the master problem: "For any future choice of :math:`x`, the cost of the corresponding subproblem
        :math:`\eta` will be at least :math:`\bar{\pi}^T (b - A x)`."

    *   It can also be seen as a first-order
        Taylor approximation (or linearization) of :math:`\eta` around :math:`\bar{x}`, since the cut is equivalent to

        .. math::

            \eta \geq \bar{\pi}^T (b - A \bar{x}) - \bar{\pi}^T A (x - \bar{x})

        where :math:`\bar{\pi}^T (b - A \bar{x}) = f^T \bar{y}` (strong duality) is
        the optimal value of the subproblem at :math:`\bar{x}`,
        and :math:`-\bar{\pi}^T A` is the gradient of the optimal value function :math:`\eta` with respect to :math:`x`.

    *   The former form is more generally used in practice, as it does not require storing :math:`\bar{x}`.


Feasibility Cut
^^^^^^^^^^^^^^^^^

*   **When is it generated?** When the subproblem is infeasible for a given :math:`\bar{x}`.
    This corresponds to the dual subproblem being unbounded.

*   **What is the logic?** If the dual is unbounded, we can find an *extreme ray* :math:`\bar{r}` of
    the dual feasible region. An extreme ray is a direction in which the dual objective can increase indefinitely.
    The condition for the dual being unbounded for :math:`\bar{x}` is :math:`\bar{r}^T (b - A \bar{x}) > 0`.
    To prevent future choices of :math:`x` from causing the same infeasibility, we must enforce the opposite.

*   **The Cut:** We add the following linear constraint to the master problem.

    .. math::
       0 \geq \bar{r}^T (b - A x)

.. note::

    *   This cut tells the master problem: "The choice :math:`\bar{x}` was invalid because it made the subproblem
        impossible to solve. This constraint cuts off solutions similar to :math:`\bar{x}`."

    *   An extreme ray is a *certificate of infeasibility*. Its existence is guaranteed by
        `Farkas' Lemma <https://en.wikipedia.org/wiki/Farkas%27_lemma>`_,
        and it can be obtained directly from LP solvers when they declare a problem to be infeasible.

    *   **Farkas' Lemma**: For the matrices :math:`A, B` and vectors :math:`b, \bar{x}`, exactly one
        of the following statements is true:

        #.  *(feasible subproblem)* There exists a :math:`y \geq 0` such that
            :math:`B y = b - A\bar{x}`.

        #.  *(infeasible subproblem)* There exists a :math:`r \in \mathbb{R}` such that
            :math:`B^T r \leq 0` and :math:`r^T(b - A\bar{x}) > 0`.



Algorithm
-----------------------------------

The algorithm is an iterative process that alternates between solving the master problem, solving the subproblem,
and adding Benders cuts to the master problem based on the subproblem's results.

#. **Initialization**

   *   Initialize a lower bound :math:`LB = -\infty` and an upper bound :math:`UB = +\infty`.
   *   Add any initial cuts to the master problem if available. Often, the algorithm starts with no cuts.
   *   Set the iteration counter :math:`k = 1`.

#. **Step 1: Solve the master problem**

   *   Solve the current master problem to get a solution :math:`(\bar{x}_k, \bar{\eta}_k)`.
   *   The objective value of the master problem, :math:`c^T \bar{x}_k + \bar{\eta}_k`, is a valid lower bound on
       the optimal solution of the original problem. Update :math:`LB = \max(LB, c^T \bar{x}_k + \bar{\eta}_k)`.

#. **Step 2: Check for convergence**

   *   If :math:`UB - LB \leq \epsilon` (where :math:`\epsilon` is a small tolerance), then **STOP**.
       The optimal solution has been found within the desired tolerance.
       The best solution found so far that yielded a feasible subproblem is the optimal solution.

#. **Step 3: Solve the subproblem**

   *   Using the fixed value :math:`\bar{x}_k` from the master problem, solve the (dual) subproblem.

#. **Step 4: Generate and add a cut**

   *   **Case A: subproblem is feasible (dual is bounded).**

          *   The sub problem objective value is :math:`f^T \bar{y}_k = \bar{\pi}^T_k (b - A \bar{x}_k)`.
          *   The objective value for this feasible solution is :math:`c^T \bar{x}_k + f^T \bar{y}_k`.
          *   Update the upper bound by :math:`UB = \min(UB, c^T \bar{x}_k + f^T \bar{y}_k)`.
          *   Add a **Benders optimality cut** to the master problem for lower bounding :math:`\eta`.

   .. caution::

        *   For :math:`-\infty < \eta < +\infty` introduced in the master problem for optimality cuts,
            :math:`\infty` should be replaced with a sufficiently large number,
            that remains as small as possible to ensure validity, to avoid numerical issues in practice.
        *   In BendersLib, :math:`-\infty` is provided as a customizable parameter :attr:`BendersParams.theta_lb`;
            :math:`+\infty` is set to solvers' default upper bound for unbounded variables.

   *   **Case B: subproblem is infeasible (dual is unbounded).**

        * Find an extreme ray and add a **Benders feasibility cut** to the master problem.


#. **Step 5: Loop**

   *   Increment :math:`k = k + 1` and go back to **Step 1**.


Given the set of complicating variables, the classical Benders Decomposition method has a standard way to
formulate the master problem, subproblem, and Benders cuts.
Therefore, these procedures can be automated, and users only need to provide the original problem
and specify which variables are complicating variables.
We implemented the method in :class:`~benderslib.ClassicalBenders`, and automated it in
:class:`~benderslib.AnnotatedBenders`.

.. seealso::

    * Rahmaniani et al. [#]_ and Aardal et al. [#]_ also provide the method's mathematical formulation.
    * BendersLib's implementation of optimality and feasibility cuts: :class:`ClassicalOC` and :class:`ClassicalFC`.
    * BendersLib's implementation of the Benders method: :class:`ClassicalBenders`.
    * **Examples**: :doc:`../examples/basic/classical_benders`, :doc:`../examples/basic/annotated_benders`, and more (:doc:`benders: classical <../_tags/benders-classical>`).

References
------------------------------

.. [#] Benders, J. F. (1962). Partitioning procedures for solving mixed-variables programming problems. Numerische Mathematik, 4(1), 238–252. https://doi.org/10.1007/BF01386316
.. [#] Rahmaniani, R., Crainic, T. G., Gendreau, M., & Rei, W. (2017). The Benders Decomposition algorithm: A literature review. European Journal of Operational Research, 259(3), 801–817. https://doi.org/10.1016/j.ejor.2016.12.005
.. [#] Aardal, K., Hurkens, C., & Lenstra, J. K. (2025). Jacques Benders and his decomposition algorithm. Operations Research Letters, 63, 107361. https://doi.org/10.1016/j.orl.2025.107361

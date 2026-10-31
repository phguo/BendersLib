L-shaped Method
=====================================

.. currentmodule:: benderslib

.. role:: raw-latex(raw)
   :format: latex

.. default-role:: raw-latex

The L-shaped method [1]_ is a specific application of Benders decomposition tailored for **two-stage stochastic linear programming**.
These problems involve making a decision now (first stage) in the face of uncertainty about the future, which is revealed later (second stage).
The problem structure consists of first-stage decisions that must hold for all future scenarios, and second-stage (*recourse*) decisions
that adapt to the outcome of a specific scenario.

.. note::
    The relationship between the L-shaped method and the :doc:`../tutorials/classical` (see `StackExchange/OR <https://or.stackexchange.com/q/10695/8718>`_):

    *   They are essentially the **same**.
        (*"In Section 2, an algorithm which is essentially the same as the algorithm developed by Benders is described and a geometric interpretation is given."* [1]_
        This was explicitly noted by Van Slyke and Wets in their original 1969 paper [1]_ introducing the L-shaped method).
    *   In the literature, the term **"L-shaped method"** is reserved for two-stage stochastic programming problems,
        while **"Benders decomposition"** is a more general technique, sometimes it is interchangeably used for two-stage stochastic programs as well.

Original Problem
-----------------

Let :math:`x` be the first-stage decision variables and :math:`y` be the second-stage decision variables.
The uncertainty is modeled through a set of discrete scenarios :math:`\Omega`, where each scenario :math:`\omega \in \Omega`
occurs with a probability :math:`p_\omega`. The **deterministic equivalent** of a two-stage stochastic program is as

.. math::
   \begin{aligned}
   \min_{x, y_\omega} \quad & c^T x + \sum_{\omega \in \Omega} p_\omega q_\omega^T y_\omega \\
   \text{s.t.} \quad & Ax \geq b \\
                     & T_\omega x + W y_\omega \geq h_\omega, \quad \forall \omega \in \Omega \\
                     & x \in X \\
                     & y_\omega \in Y, \quad \forall \omega \in \Omega
   \end{aligned}

where :math:`x` are the first-stage (here-and-now) variables, which are the complicating variables.
:math:`y_\omega` are the second-stage (wait-and-see) variables for each scenario :math:`\omega`.
The first-stage constraints :math:`Ax \geq b` are independent of any scenario.
The second-stage constraints :math:`T_\omega x + W y_\omega \geq h_\omega` link the first-stage decisions to the second-stage decisions.
The matrix :math:`W` is known as the *recourse matrix* and is typically assumed to be fixed across scenarios.

.. note::
    Assumptions commonly made in the L-shaped method include:

    *   **Linear recourse**: The second-stage problem is a Linear Programming problem for each scenario.
    *   **Fixed recourse**: The recourse matrix :math:`W` is the same for all scenarios.
    *   **Complete recourse**: The second-stage problem is always feasible for any first-stage decision :math:`x`.

The method's name originates from the block structure of the constraint matrix in the deterministic
equivalent formulation. When the variables are ordered with the first-stage variables :math:`x` first,
followed by the recourse variables :math:`y_\omega` for each scenario, the matrix of constraint coefficients
has a clear **"L" shape**. The first-stage constraint matrix :math:`A` forms the top horizontal bar, and the technology
matrices :math:`T_\omega` stack vertically below it. The recourse matrix :math:`W` forms a block-diagonal pattern,
and the top-right of the overall matrix is all zeros.

.. _tutorials-lshaped-block:

.. math::
   \begin{pmatrix}
       A      & 0      & 0      & \cdots & 0   \\
       T_1    & W      & 0      & \cdots & 0   \\
       T_2    & 0      & W      & \cdots & 0   \\
       \vdots & \vdots & \vdots & \ddots & \vdots \\
       T_{|\Omega|} & 0 & 0 & \cdots & W
   \end{pmatrix}

This structure is the key to the decomposition. Since the second-stage blocks are independent of one another,
fixing the first-stage variables :math:`x` causes the problem to "decompose" into smaller parallel subproblems.



Reformulation
------------------

The problem is reformulated by separating the first-stage variables from the second-stage variables. The second-stage costs
and constraints are handled in subproblems that are solved for each scenario independently.
The **master problem** is defined over the first-stage variables :math:`x` and an auxiliary variable :math:`\theta`
that represents the expected future cost of the second-stage decisions.

.. math::
   \begin{aligned}
   \min_{x, \theta} \quad & c^T x + \theta \\
   \text{s.t.} \quad & Ax \geq b \\
                     & x \in X \\
                     & \theta \geq \dots (\text{optimality cuts}) \\
                     & 0 \geq \dots (\text{feasibility cuts})
   \end{aligned}

For a given first-stage decision :math:`\bar{x}`, the second-stage problem decomposes into :math:`|\Omega|` independent
linear programs, one for each scenario :math:`\omega`.
The **primal subproblem** for scenario :math:`\omega` is as follows.

.. math::
   \begin{aligned}
   Q(\bar{x}, \omega) = \min_{y_\omega} \quad & q_\omega^T y_\omega \\
   \text{s.t.} \quad & W y_\omega \geq h_\omega - T_\omega \bar{x} \\
                     & y_\omega \in Y
   \end{aligned}

As in classical Benders, we are interested in the dual of the subproblem to generate cuts.
The **dual subproblem** for scenario :math:`\omega` is as follows.

.. math::
   \begin{aligned}
   \max_{\pi_\omega} \quad & \pi_\omega^T (h_\omega - T_\omega \bar{x}) \\
   \text{s.t.} \quad & W^T \pi_\omega \leq q_\omega \\
                     & \pi_\omega \geq 0
   \end{aligned}

The solution to these dual subproblems provides the necessary information to generate feasibility and optimality cuts for the master problem.

.. hint::
    An attractive feature of the L-shaped method is that the subproblems for each scenario can be solved in parallel,
    making it well-suited for large-scale stochastic programming problems with many scenarios.


L-shaped Cuts
-------------

The cuts improve the master problem's estimate of the expected second-stage cost.
Feasibility cuts are created when a subproblem is infeasible,
whereas optimality cuts arise when all subproblems are feasible.
Optimality cuts come in two forms: single-cut and multi-cut.

Feasibility Cut
^^^^^^^^^^^^^^^^^
A feasibility cut is generated if, for a given :math:`\bar{x}`, the subproblem for some scenario :math:`\omega` is infeasible.
This corresponds to the dual subproblem for that scenario being unbounded. An extreme ray :math:`\bar{r}_\omega`
of the dual feasible region provides a certificate of infeasibility.

*   **When is it generated?** When a subproblem for scenario :math:`\omega` is infeasible.
*   **The Cut:** To cut off the infeasible :math:`\bar{x}`, we add the constraint as follows.

    .. math::
       0 \geq \bar{r}_\omega^T (h_\omega - T_\omega x)

This cut makes any first-stage decision :math:`x` that would cause the same infeasibility in scenario :math:`\omega` invalid.

.. note::
    *  On may chose to add feasibility cuts for all infeasible scenarios found in an iteration,
       or just for the first one encountered (the subsequent subproblems is not required to be solved).
    *  The above feature can be controlled in BendersLib via the :attr:`BendersParams.multi_feas_cut` parameter.

Optimality Cut
^^^^^^^^^^^^^^^^^^
An optimality cut is generated when the subproblems for all scenarios :math:`\omega \in \Omega` are feasible for a given :math:`\bar{x}`.
This yields an optimal dual solution :math:`\bar{\pi}_\omega` for each scenario. There are two common ways to formulate optimality cuts.

Single Optimality Cut
""""""""""""""""""""""
The single-cut approach, also known as the classical L-shaped method, adds one aggregated cut to the master problem per iteration.

*   **When is it generated?** When all subproblems are feasible for the given :math:`\bar{x}`, but the subproblem solutions
    suggest that the estimator :math:`\theta` in the master problem underestimates the true expected recourse cost.

*   **Logic:** The variable :math:`\theta` in the master problem represents the expected future cost,
    :math:`\mathbb{E}[Q(x, \omega)] = \sum_{\omega \in \Omega} p_\omega Q(x, \omega)`. The cut provides a lower bound on this expectation.
    Using the optimal dual solutions :math:`\bar{\pi}_\omega`, we construct a valid lower bound for any :math:`x`.

*   **The Cut:** The aggregated cut is as follows.

    .. math::
       \theta \geq \sum_{\omega \in \Omega} p_\omega \left[ \bar{\pi}_\omega^T (h_\omega - T_\omega x) \right]

This cut is a linearization of the convex expected recourse function :math:`\mathbb{E}[Q(x, \omega)]` at the point :math:`\bar{x}`.

Multi Optimality Cut
"""""""""""""""""""""
The multi-cut approach generates a separate cut for each scenario, leading to a tighter but larger master problem,
since the number of cuts added per iteration equals the number of scenarios.

*   **When is it generated?** When all subproblems are feasible for the given :math:`\bar{x}`, but the subproblem solutions
    suggest that the estimator :math:`\theta_\omega` in the master problem underestimate the true recourse cost for
    the corresponding scenario.

*   **Logic:** First, the master problem is reformulated to include a separate recourse cost variable :math:`\theta_\omega` for each scenario.
    The master problem then becomes as follows.

    .. math::
       \begin{aligned}
       \min_{x, \theta_\omega} \quad & c^T x + \sum_{\omega \in \Omega} p_\omega \theta_\omega \\
       \text{s.t.} \quad & Ax \geq b \\
                         & x \in X \\
                         & \theta_\omega \geq \dots (\text{optimality cuts for } \omega), \forall \omega \in \Omega \\
                         & 0 \geq \dots (\text{feasibility cuts})
       \end{aligned}

*   **The Cut:** For each scenario :math:`\omega`, a separate optimality cut is added to the master problem. This cut is identical in form to the classical Benders optimality cut, applied to a single subproblem.

    .. math::
       \theta_\omega \geq \bar{\pi}_\omega^T (h_\omega - T_\omega x)

.. note::
    *   **Single-cut vs. Multi-cut:**

        * The single-cut method adds only one optimality cut per iteration, keeping the master problem smaller.
          However, it may require more iterations to converge due to the coarser approximation of the recourse function.
        * The multi-cut approach provides a more accurate piecewise linear approximation of the recourse function,
          so it typically converges in fewer iterations than the single-cut method. However, the master problem grows
          larger with each iteration, potentially increasing the time per iteration.

    *   Users can control which variant to use in BendersLib via the :attr:`BendersParams.multi_opti_cut` parameter.


Algorithm
-----------------------------------

The L-shaped algorithm proceeds as follows, shown here for the single-cut and multi-cut variants.

#. **Initialization**

   *   Initialize lower bound :math:`LB = -\infty` and upper bound :math:`UB = +\infty`.
   *   Set iteration counter :math:`k = 1`.

#. **Step 1: Solve the master problem**

   *   Solve the current master problem to get a solution :math:`(\bar{x}_k, \bar{\theta}_k)`.
   *   Update the lower bound: :math:`LB = \max(LB, c^T \bar{x}_k + \bar{\theta}_k)`.

#. **Step 2: Check for convergence**

   *   If :math:`UB - LB \leq \epsilon`, **STOP**. The optimal solution is found.

#. **Step 3: Solve the subproblems**

   *   For each scenario :math:`\omega \in \Omega`, solve the (dual) subproblem with the fixed value :math:`\bar{x}_k`.

#. **Step 4: Generate and add a cut**

   *   **Case A: A subproblem is infeasible.**

      *   Let scenario :math:`\omega_j` be the first one found to be infeasible.
      *   Obtain an extreme ray :math:`\bar{r}_{\omega_j}` from its dual subproblem.
      *   Add a **feasibility cut** to the master problem:
          :math:`0 \geq \bar{r}_{\omega_j}^T (h_{\omega_j} - T_{\omega_j} x)`.

   .. note::
        When :attr:`BendersParams.multi_feas_cut` is set to ``True``, feasibility cuts are added for all infeasible scenarios.
        BendersLib will filter out duplicate cuts automatically.

   *   **Case B: All subproblems are feasible.**

      *   Obtain the optimal dual solutions :math:`\bar{\pi}_\omega` for all :math:`\omega \in \Omega`.
      *   Calculate the expected recourse cost:
          :math:`Q(\bar{x}_k) = \sum_{\omega \in \Omega} p_\omega \left[ \bar{\pi}_\omega^T (h_\omega - T_\omega \bar{x}_k) \right]`.
      *   Update the upper bound: :math:`UB = \min(UB, c^T \bar{x}_k + Q(\bar{x}_k))`.
      *   Add optimality cut to the master problem:

          *   **Single optimality cut**:
              :math:`\theta \geq \sum_{\omega \in \Omega} p_\omega \left[ \bar{\pi}_\omega^T (h_\omega - T_\omega x) \right]`.
          *   **Multi optimality cut**:
              :math:`\theta_\omega \geq \bar{\pi}_\omega^T (h_\omega - T_\omega x)` for each :math:`\omega`
              that :math:`\bar{\theta}_\omega < \bar{\pi}_\omega^T (h_\omega - T_\omega \bar{x}_k)`,
              where :math:`\bar{\pi}_\omega^T (h_\omega - T_\omega \bar{x}_k)` is the objective value of the subproblem for scenario :math:`\omega`.

   .. note::
        When :attr:`BendersParams.multi_opti_cut` is set to ``True``, multi optimality cuts are added.
        They are only added for scenarios where the current estimate underestimates the true recourse cost.

#. **Step 5: Loop**

   *   Increment :math:`k = k + 1` and go back to **Step 1**.


The L-shaped method requires master and subproblem formulations that align with the two-stage stochastic programming structure.
We implemented it in :class:`LShaped`.
Users may formulate their problems to deterministic equivalents manually for comparison or benchmarking purposes.


.. seealso::
    * Birge and Louveaux [#]_ and Shapiro et al. [#]_ provide textbooks on stochastic programming, covering the L-shaped method.
    * BendersLib's implementation of the L-shaped optimality cuts:
      :class:`LShapedOC` (single-cut & linear recourse), :class:`ClassicalOC` (multi-cut & linear recourse),
      :class:`GeneLShapedOC` (single-cut & convex recourse), and :class:`GeneralizedOC` (multi-cut & convex recourse).
    * BendersLib's implementation of the feasibility cut: :class:`ClassicalFC`.
    * BendersLib's implementation of the L-shaped methods:
      :class:`LShaped` (linear recourse) and :class:`GeneLShaped` (convex recourse).
    * **Examples**: :doc:`../examples/basic/lshaped`, :doc:`../examples/basic/glshaped`, and more (:doc:`benders: l-shaped <../_tags/benders-l-shaped>`).


References
------------------------------

.. [1] Van Slyke, R. M., & Wets, R. (1969). L-shaped linear programs with applications to optimal control and stochastic programming. SIAM Journal on Applied Mathematics, 17(4), 638–663. https://doi.org/10.1137/0117061
.. [#] Birge, J. R., & Louveaux, F. (2011). Introduction to Stochastic Programming. Springer New York. https://doi.org/10.1007/978-1-4614-0237-4
.. [#] Shapiro, A., Dentcheva, D., & Ruszczynski, A. (2021). Lectures on Stochastic Programming: Modeling and Theory (3rd ed.). Society for Industrial and Applied Mathematics. https://doi.org/10.1137/1.9781611976595

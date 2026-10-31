Integer L-shaped Method
================================

.. currentmodule:: benderslib

.. role:: raw-latex(raw)
   :format: latex

.. default-role:: raw-latex

The Integer L-shaped method [1]_ extends the :doc:`cbd` and :doc:`lshaped` to handle **two-stage stochastic integer programming**
with binary complicating variables in the first stage and integer recourse variables in the second stage.
In these problems, the second-stage (recourse) decisions include integer variables, making the subproblems MILP rather than simple LP.
Because MILPs do not have a strong, readily-available dual like LPs do, the classical Benders cuts derived from duality are not applicable.
Instead, the Integer L-shaped method applies the principles of :doc:`cbd` to the stochastic programming framework.

Original Problem
-----------------

The problem structure is similar to that of the standard L-shaped method, but the second-stage variables now belong to a set that includes integers.

.. math::
   \begin{aligned}
   \min_{x, y_\omega} \quad & c^T x + \sum_{\omega \in \Omega} p_\omega q_\omega^T y_\omega \\
   \text{s.t.} \quad & Ax \geq b \\
                     & T_\omega x + W y_\omega \geq h_\omega, \quad \forall \omega \in \Omega \\
                     & x \in X \subseteq \{0,1\}^n \\
                     & y_\omega \in Y_\omega, \quad \forall \omega \in \Omega
   \end{aligned}

The key differences from the :doc:`lshaped` are:

*   The first-stage complicating variables :math:`x` are required to be **binary** for generating combinatorial cuts.
*   The second-stage feasible region :math:`Y_\omega` contains **integer** variables, no longer just continuous ones.

Reformulation
------------------

The decomposition into a master problem and subproblems remains, but the nature of the cuts and the information gathered from subproblems changes.
The **master problem** is defined over the first-stage binary variables :math:`x` and an auxiliary variable :math:`\theta` that estimates the expected recourse cost.

.. math::
   \begin{aligned}
   \min_{x, \theta} \quad & c^T x + \theta \\
   \text{s.t.} \quad & Ax \geq b \\
                     & x \in X \subseteq \{0,1\}^n \\
                     & \dots (\text{no-good cuts}) \\
                     & \dots (\text{integer optimality cuts})
   \end{aligned}

For a given first-stage decision :math:`\bar{x}`, the **subproblem** for each scenario :math:`\omega` is a MILP as follows.

.. math::
   \begin{aligned}
   Q(\bar{x}, \omega) = \min_{y_\omega} \quad & q_\omega^T y_\omega \\
   \text{s.t.} \quad & W y_\omega \geq h_\omega - T_\omega \bar{x} \\
                     & y_\omega \in Y_\omega
   \end{aligned}

Solving this subproblem can result in two outcomes:

1.  **Infeasible**: Leads to a **no-good cut** (feasibility cut) for the master problem.
2.  **Feasible**: Yields an optimal solution :math:`\bar{y}_\omega` and cost :math:`Q_\omega^*`, leading to an **integer optimality cut**.


Integer L-shaped Cuts
----------------------

Since LP duality cannot be used, the cuts are logic-based, identifying the specific combination of first-stage decisions :math:`x` that caused either infeasibility or a certain level of cost in a subproblem.

No-good Cut (Feasibility Cut)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*   **When is it generated?** When the subproblem for a specific scenario :math:`\omega` is found to be infeasible for a given first-stage solution :math:`\bar{x}`.

*   **Logic:** A no-good cut forbids the exact combination of master variables that led to the infeasibility.
    Let :math:`I_1` be the indices of binary master variables :math:`x_i` that are 1 in :math:`\bar{x}`, and :math:`I_0` be the indices of those that are 0. The cut forces at least one of these variables to change its value.

*   **The Cut:**

    .. math::
       \sum_{i \in I_1} (1 - x_i) + \sum_{i \in I_0} x_i \geq 1

.. note::
    *   This cut is identical in form to the no-good cut in :doc:`cbd`.
    *   To strengthen the cut, the sets :math:`I_1` and :math:`I_0` should ideally form a minimal set of variables causing infeasibility,
        which can be found by solving for an :abbr:`Irreducible Inconsistent Subsystem (a minimal subset of constraints and/or variable bounds that cause the infeasibility)` (IIS) of the subproblem.

Integer Optimality Cut
^^^^^^^^^^^^^^^^^^^^^^^^^

*   **When is it generated?** When all subproblems are feasible for a given :math:`\bar{x}`, yielding optimal costs :math:`Q_\omega^*`.

*   **From Logic to Math:** The cut is derived from a simple logical statement, which is then translated into a linear inequality using a "big-M" approach.
    We show this for the single-cut case.

Single Integer Optimality Cut
""""""""""""""""""""""""""""""
This cut provides a lower bound on the expected recourse cost :math:`\theta`.

*   **The Core Logic:** The cut must enforce the following condition:
    **IF** the master problem chooses the same solution again (i.e., :math:`x = \bar{x}`),
    **THEN** the expected future cost :math:`\theta` must be greater than or equal to the cost :math:`Q^* = \sum_{\omega \in \Omega} p_\omega Q_\omega^*` calculated,
    **ELSE** (if :math:`x \neq \bar{x}`), this specific cut should not impose a new bound and must be relaxed.

    .. math::
       x = \bar{x} \implies \theta \geq Q^*

*   **Linear Formulation:** This logic is modeled by introducing a large constant :math:`M`.
    The expression :math:`\sum_{i \in I_1} (1 - x_i) + \sum_{i \in I_0} x_i` is 0 if :math:`x=\bar{x}` and at least 1 otherwise.
    This gives us the "big-M" cut as follows.

    .. math::
       \theta \geq Q^* - M \left( \sum_{i \in I_1} (1 - x_i) + \sum_{i \in I_0} x_i \right)

    .. note::
        This is the form used in the :doc:`cbd`.

    It is equivalent to the following form.

    .. math::
       \theta \geq Q^* - M \left( |I_1| - \sum_{i \in I_1} x_i + \sum_{i \in I_0} x_i \right)

*   **Choosing M:**
    Laporte & Louveaux [1]_ provide a tighter form by refining the choice of :math:`M`.
    The tightest valid value for :math:`M` is :math:`(Q^* - L)`, where :math:`L` is a known lower
    bound on :math:`\theta`.
    Substituting this gives the following cut.

    .. math::
       \theta \geq Q^* - (Q^* - L) \left( |I_1| - \sum_{i \in I_1} x_i + \sum_{i \in I_0} x_i \right)

    It can be rearranged to the final form [1]_ as follows.

    .. math::
       \theta \geq (Q^* - L) \left ( \sum_{i \in I_1} x_i - \sum_{i \in I_0} x_i \right ) - (Q^* - L) (|I_1| - 1) + L

    .. note::
       How to choose the value of :math:`L`:

       * :math:`L` can be a trivial lower bound 0.
       * :math:`L` can also be the value of :math:`\theta` from the previous iteration,
         which is valid since :math:`\theta` is non-decreasing over iterations.

Multi Integer Optimality Cut
"""""""""""""""""""""""""""""""

Similar to the :doc:`lshaped`, a multi-cut version can be derived where each scenario contributes its own cut.

*   **Logic:** A separate recourse cost variable :math:`\theta_\omega` is introduced for each scenario in the master problem,
    with the objective :math:`c^T x + \sum_{\omega \in \Omega} p_\omega \theta_\omega`. A separate optimality cut is added for each scenario.

*   **The Cut:** The cut for each scenario :math:`\omega` is as follows.

    .. math::
       \theta_\omega \geq (Q_\omega^* - L_\omega) \left ( \sum_{i \in I_1} x_i - \sum_{i \in I_0} x_i \right ) - (Q_\omega^* - L_\omega) (|I_1| - 1) + L_\omega

    Here, :math:`Q_\omega^*` is the optimal cost from scenario :math:`\omega` subproblem,
    and :math:`L_\omega` is a lower bound on the individual recourse cost :math:`\theta_\omega`.

.. note::
    The tradeoff between single-cut and multi-cut in the :doc:`lshaped` is also relevant to the Integer L-shaped method.

    *   **Single-cut vs. Multi-cut:**

        * The single-cut method adds only one optimality cut per iteration, keeping the master problem smaller.
          However, it may require more iterations to converge due to the coarser approximation of the recourse function.
        * The multi-cut approach provides a more accurate piecewise linear approximation of the recourse function,
          so it typically converges in fewer iterations than the single-cut method. However, the master problem grows
          larger with each iteration, potentially increasing the time per iteration.

    BendersLib provides parameters :attr:`BendersParams.multi_opti_cut` and :attr:`BendersParams.multi_feas_cut` to select the desired approach.

Algorithm
-----------------------------------

The iterative procedure combines the loops of the :doc:`lshaped` method with the cut generation logic of the :doc:`cbd`.

#. **Initialization**

   *   Initialize lower bound :math:`LB = -\infty` and upper bound :math:`UB = +\infty`.
   *   Set iteration counter :math:`k = 1`.

#. **Step 1: Solve the master problem**

   *   Solve the current master problem to get a solution :math:`(\bar{x}_k, \bar{\theta}_k)`.
   *   Update the lower bound: :math:`LB = \max(LB, c^T \bar{x}_k + \bar{\theta}_k)`.

#. **Step 2: Check for convergence**

   *   If :math:`UB - LB \leq \epsilon`, **STOP**. The optimal solution is found.

#. **Step 3: Solve the subproblems**

   *   For each scenario :math:`\omega \in \Omega`, solve the subproblem with :math:`x` fixed to :math:`\bar{x}_k`.

#. **Step 4: Generate and add a cut**

   *   **Case A: A subproblem is infeasible.**

      *   Let scenario :math:`\omega_j` be the first one found to be infeasible.
      *   For the scenario :math:`\omega_j`, identify the sets :math:`(I_1, I_0)`.
      *   Add a **no-good cut** to the master problem:
          :math:`\sum_{i \in I_1} (1 - x_i) + \sum_{i \in I_0} x_i \geq 1`.

   .. note::
        When :attr:`BendersParams.multi_feas_cut` is set to ``True``, feasibility cuts are added for all infeasible scenarios.
        BendersLib will filter out duplicate cuts automatically.

   *   **Case B: All subproblems are feasible.**

      *   For each scenario :math:`\omega`, get an optimal subproblem cost :math:`Q_\omega^*`.
      *   Calculate the objective for this feasible solution: :math:`c^T \bar{x}_k + \sum_{\omega \in \Omega} p_\omega Q_\omega^*`.
      *   Update the upper bound: :math:`UB = \min(UB, c^T \bar{x}_k + \sum_{\omega \in \Omega} p_\omega Q_\omega^*)`.
      *   Add an **integer optimality cut** (either single-cut or multi-cut version) to the master problem.
          In the multi-cut case, cuts are only added for scenarios where :math:`\bar{\theta}_{\omega} < Q_\omega^*`.

   .. note::
        When :attr:`BendersParams.multi_opti_cut` is set to ``True``, multi optimality cuts are added.
        They are only added for scenarios where the current estimate underestimates the true recourse cost.

#. **Step 5: Loop**

   *   Increment :math:`k = k + 1` and go back to **Step 1**.

.. seealso::
    *   Rahmaniani et al. [#]_ discussed Benders decomposition with discrete subproblems.
    *   See :doc:`lshaped` for the basis for the two-stage stochastic programming structure.
    *   See :doc:`cbd` for the basis for the no-good cut and combinatorial optimality cut.
    * BendersLib's implementation of optimality and feasibility cuts: :class:`CombinatorialOC` and :class:`NoGoodFC`.
    * BendersLib's implementation of the Integer L-shaped method: :class:`IntegerLShaped`.
    * **Examples**: :doc:`../examples/basic/ilshaped`, :doc:`../examples/advanced/ilshaped_iis`, and more (:doc:`benders: integer l-shaped <../_tags/benders-integer-l-shaped>`).


References
------------------------------

.. [1] Laporte, G., & Louveaux, F. V. (1993). The integer L-shaped method for stochastic integer programs with complete recourse. Operations Research Letters, 13(3), 133–142. https://doi.org/10.1016/0167-6377(93)90002-X
.. [#] Rahmaniani, R., Crainic, T. G., Gendreau, M., & Rei, W. (2017). The Benders Decomposition algorithm: A literature review. European Journal of Operational Research, 259(3), 801–817. https://doi.org/10.1016/j.ejor.2016.12.005

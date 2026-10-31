Generalized Benders Decomposition
============================================

.. currentmodule:: benderslib

.. role:: raw-latex(raw)
   :format: latex

.. default-role:: raw-latex

.. danger::

    **Non-linear features in BendersLib are experimental**.

    BendersLib currently supports only **linear** Benders cuts.
    Therefore, the user must ensure that the problem is **linearly separable** as described
    in the special cases for both optimality and feasibility cuts.

The Generalized Benders Decomposition (GBD) [#]_ extends the :doc:`classical` from
Mixed-Integer Linear Programming (MILP) to a broader class of Mixed-Integer Non-Linear Programming (MINLP).
It maintains the same core idea of decomposing the problem into a master problem
and a subproblem but uses more general principles from *convex optimization*.

Original Problem
--------------------------------------------

The GBD is applied to MINLP where the variables can be partitioned into
complicating variables :math:`x` (typically integer) and easy variables :math:`y` (typically continuous),
such that when :math:`x` is fixed, the remaining problem in :math:`y` is a *convex* optimization problem.

Consider a general MINLP problem of the following form.

.. math::
   \begin{aligned}
   \min_{x, y} \quad & f(x, y) \\
   \text{s.t.} \quad & g(x, y) \leq 0 \\
                     & x \in X \\
                     & y \in Y
   \end{aligned}

In the formulation above,
:math:`f` and :math:`g` are functions, :math:`X` is
a :abbr:`non-empty compact set (A non-empty set that is both closed (contains its boundary points) and bounded (is of finite size).)`,
and :math:`Y` is a non-empty convex set.
The key assumptions for GBD are as follows.

- For any fixed :math:`\bar{x} \in X`, the functions :math:`f(\bar{x}, y)` and :math:`g(\bar{x}, y)` are *convex* in :math:`y`.
- For any fixed :math:`\bar{x} \in X`, the subproblem satisfies a constraint qualification (e.g., *Slater's condition*) to ensure strong duality.

.. admonition:: Slater's Condition
    :class: note

    `Slater's condition <https://en.wikipedia.org/wiki/Slater%27s_condition>`_
    is a *constraint qualification* in convex optimization.
    Its main purpose is to guarantee **strong duality**.
    The condition is satisfied if there exists a *strictly feasible point*
    (a point that lies in the interior of the feasible region).
    If Slater's condition holds for a convex problem,
    the optimal value of the primal problem equals the optimal value of its dual.

Reformulation
--------------------------------------------

The reformulation projects the original problem onto the space of the complicating variables :math:`x`.
A master problem is defined in terms of :math:`x` and a scalar :math:`\eta` that represents the objective value :math:`f(x,y)`.
The **master problem** is defined as follows and is
iteratively refined with cuts.

.. math::
   \begin{aligned}
   \min_{x, \eta} \quad & \eta \\
   \text{s.t.} \quad & x \in X \\
                     & \eta \geq \dots (\text{optimality cuts}) \\
                     & 0 \geq \dots (\text{feasibility cuts})
   \end{aligned}

For a candidate solution :math:`\bar{x}` from the master problem,
the **primal subproblem** is a convex Non-Linear Programming problem
that evaluates the best possible outcome for that choice of :math:`\bar{x}`.

.. math::
   v(\bar{x}) = \min_{y \in Y} \{ f(\bar{x}, y) \mid g(\bar{x}, y) \leq 0 \}

Instead of Linear Programming duality, GBD relies on the more general
`Lagrange Duality <https://en.wikipedia.org/wiki/Duality_(optimization)#Lagrange_duality>`_.
The *Lagrangian function* for the subproblem is defined as follows.

.. math::
   L(\bar{x}, y, \lambda) = f(\bar{x}, y) + \lambda^T g(\bar{x}, y)

Then the *Lagrangian dual function* is defined as follows.

.. math::
    \inf_{y \in Y} L(\bar{x}, y, \lambda) = \inf_{y \in Y} \{ f(\bar{x}, y) + \lambda^T g(\bar{x}, y) \}

.. note::

    The Lagrangian dual function is a lower bound on the optimal value of the primal subproblem for any :math:`\lambda \geq 0`.

The **Lagrangian dual subproblem** is then defined to find the optimal Lagrange multipliers :math:`\lambda`
by maximizing the Lagrangian dual function.

.. math::
    \max_{\lambda \geq 0} \inf_{y \in Y} L(\bar{x}, y, \lambda)

The optimal *Lagrange multipliers* :math:`\bar{\lambda}` for the subproblem are crucial for generating cuts.
The values of Lagrange multipliers play a similar role to values of dual variables in classical Benders Decomposition.

.. admonition:: Special Case: Separable Problems
    :class: note

    A common special case is when the functions :math:`f(x, y)` and :math:`g(x, y)`
    are separable between :math:`x` and :math:`y`.
    This property is essential for simplifying the subproblem formulation and is a prerequisite for deriving linear Benders cuts.
    This means they can be expressed as

    .. math::
       f(x, y) = f_x(x) + f_y(y)

    .. math::
       g(x, y) = g_x(x) + g_y(y)

    where :math:`f_x(x)` and :math:`g_x(x)` depend only on :math:`x`,
    and :math:`f_y(y)` and :math:`g_y(y)` depend only on :math:`y`.
    In this case, the prime subproblem simplifies to

    .. math::
       v(\bar{x}) = \min_{y \in Y} \{ f_x(\bar{x}) + f_y(y) \mid g_y(y) \leq -g_x(\bar{x}) \}.

    It Lagrangian function becomes

    .. math::
       L(\bar{x}, y, \lambda) = f_x(\bar{x}) + f_y(y) + \lambda^T (g_y(y) + g_x(\bar{x})).

    The Lagrangian dual subproblem is

    .. math::
       \max_{\lambda \geq 0} \{ f_x(\bar{x}) + \lambda^T g_x(\bar{x}) + \inf_{y \in Y} \{ f_y(y) + \lambda^T g_y(y) \} \}.

    By solving the dual subproblem we can obtain the optimal Lagrange multipliers
    and the objective value of the subproblem for generating Benders cuts.

Benders Cuts
--------------------------------------------

Generalized Optimality Cut
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*   **When is it generated?**
    When the Lagrangian dual subproblem for :math:`\bar{x}` is feasible, yielding an optimal primal solution :math:`\bar{y}`
    and optimal Lagrange multipliers :math:`\bar{\lambda}`.

*   **What is the logic?**
    For the fixed multipliers :math:`\bar{\lambda}` obtained from solving the subproblem at :math:`\bar{x}`,
    the Lagrangian dual function :math:`\inf_{y \in Y} L(x, y, \bar{\lambda})` provides a valid lower bound for the true
    value function :math:`v(x)` for all :math:`x`.
    If the Lagrange multipliers are optimal and the strong duality holds, the bound is tight at :math:`\bar{x}`.

*   **The Cut:**
    We add the following constraint to the master problem, which may be nonlinear in :math:`x`.

    .. math::
       \eta \geq \inf_{y \in Y} \{ f(x, y) + \bar{\lambda}^T g(x, y) \}

.. caution::

    BendersLib currently supports only **linear** Benders cuts.
    Therefore, the user must ensure that the problem is **linearly separable** as described below.

.. admonition:: Special Case: Linear Optimality Cuts
    :class: note

    The generalized optimality cut becomes linear in :math:`x` if the functions :math:`f(x, y)` and :math:`g(x, y)`
    meet two conditions: they are separable between :math:`x` and :math:`y`,
    and the parts involving :math:`x` are linear.

    **1. Separability**

    First, assume the functions are separable, the cut becomes

    .. math::
       \eta \geq \inf_{y \in Y} \{ f_x(x) + f_y(y) + \bar{\lambda}^T (g_x(x) + g_y(y)) \}.

    Since :math:`f_x(x)` and :math:`g_x(x)` do not depend on :math:`y`, they can be moved outside the infimum as

    .. math::
       \eta \geq f_x(x) + \bar{\lambda}^T g_x(x) + \inf_{y \in Y} \{ f_y(y) + \bar{\lambda}^T g_y(y) \}

    where :math:`\inf_{y \in Y} \{ f_y(y) + \bar{\lambda}^T g_y(y) \}` is a constant.
    It can be nonlinear due to :math:`f_x(x)` and :math:`g_x(x)`.

    **2. Linearity in x**

    If we further assume the functions are linear with respect to :math:`x`, i.e., :math:`f_x(x) = c^T x`
    and :math:`g_x(x) = - A x`, the cut simplifies to a linear expression

    .. math:: \eta \geq c^T x - \bar{\lambda}^T A x + K(\bar{\lambda}),
        :label: gbd_opt_cut_linear

    where :math:`K(\bar{\lambda}) = \inf_{y \in Y} \{ f_y(y) + \bar{\lambda}^T g_y(y) \}` is a constant,
    implying the cut is a linear inequality in :math:`x`.
    Note that here we use :math:`-A` as coefficient matrix to be consistent with the :doc:`classical` formulation.
    Consider the constraint :math:`Ax + Dy \geq b` (:math:`\geq` constraint) in the :doc:`classical`.
    It can be rewritten as :math:`b - Ax - Dy \leq 0` (:math:`\leq` constraint) in the :math:`g(x,y) \leq 0` format used here.
    Therefore, the coefficient matrix for :math:`x` in :math:`g(x,y)` is :math:`-A`.

.. admonition:: Transforming to Classical Benders Cut
    :class: note

    **If the linearly separable conditions are met, the generalized optimality cut can be transformed into
    the first-order Taylor approximation form of classical Benders optimality cut.**

    For a given :math:`\bar{x}`, let (:math:`\bar{y}`, :math:`\bar{\lambda}`) be the optimal dual solution.
    The primal subproblem objective is :math:`f_x(\bar{x}) + f_y(\bar{y})`.
    The dual subproblem objective is :math:`f_x(\bar{x}) + \bar{\lambda}^T g_x(\bar{x}) + \inf_{y \in Y} \{ f_y(y) + \bar{\lambda}^T g_y(y) \}`.
    By strong duality, they are equal.
    Using the definitions :math:`f_x(x) = c^T x`, :math:`g_x(x) = - A x`, and :math:`K(\bar{\lambda}) = \inf_{y \in Y} \{ f_y(y) + \bar{\lambda}^T g_y(y) \}`, we get

    .. math::
       c^T \bar{x} + f_y(\bar{y}) = c^T \bar{x} - \bar{\lambda}^T A \bar{x} + K(\bar{\lambda}).

    This simplifies to an expression for :math:`K(\bar{\lambda})`

    .. math::
       K(\bar{\lambda}) = f_y(\bar{y}) + \bar{\lambda}^T A \bar{x}.

    Substituting this back into :eq:`gbd_opt_cut_linear`, we have

    .. math::
       \eta \geq c^T x - \bar{\lambda}^T A x + (f_y(\bar{y}) + \bar{\lambda}^T A \bar{x}).

    By rearranging terms, we get

    .. math::
       \eta - c^T x \geq f_y(\bar{y}) - \bar{\lambda}^T A (x - \bar{x}).

    This simplifies to the classical Benders optimality cut (first-order Taylor approximation form)

    .. math:: \eta' \geq f_y(\bar{y}) - \bar{\lambda}^T A (x - \bar{x}) \quad \text{[Optimality Cut]}
        :label: gbd_oc

    where :math:`\eta' = \eta - c^T x` is the estimator variable with the same definition in the :doc:`classical`.

.. tip::

    When the **linearly separable** condition is satisfied,
    and we have a **black-box nonlinear solver** that can provide the **optimal objective value and Lagrange multipliers**
    of convex Non-Linear Programming problems, the generalized optimality cut can be implemented using :eq:`gbd_oc`.

Generalized Feasibility Cut
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*   **When is it generated?**
    When the primal subproblem for a given :math:`\bar{x}` is infeasible.
    This means there is no :math:`y \in Y` that satisfies the constraints :math:`g(\bar{x}, y) \leq 0`.

*   **What is the logic?**
    If the subproblem is infeasible, we need to add a constraint to the master problem to cut off
    the region of :math:`x` values that leads to this infeasibility.
    This is achieved using a generalization of `Farkas' Lemma <https://en.wikipedia.org/wiki/Farkas%27_lemma>`_:
    if the set :math:`\{ y \in Y \mid g(\bar{x}, y) \leq 0 \}` is empty, then there exists
    a vector :math:`\bar{\mu} \geq 0`, :math:`\bar{\mu} \neq 0`, such that for all :math:`y \in Y`,
    :math:`\bar{\mu}^T g(\bar{x}, y) > 0`. Or equivalently,

    .. math::
       \inf_{y \in Y} \{ \bar{\mu}^T g(\bar{x}, y) \} > 0.

*   **The Cut:**
    The feasibility cut forces any new candidate solution :math:`x` to satisfy the condition
    that would have made the subproblem feasible. The cut added to the master problem is

    .. math:: \inf_{y \in Y} \{ \bar{\mu}^T g(x, y) \} \leq 0.
        :label: gbd_feas_cut

.. caution::

    BendersLib currently supports only **linear** Benders cuts.
    Therefore, the user must ensure that the problem is **linearly separable** as described below.

.. admonition:: Special Case: Linear Feasibility Cuts
    :class: note

    Similar to the optimality cut, the generalized feasibility cut becomes linear if the
    function :math:`g(x, y)` is separable and linear in :math:`x`.

    **1. Separability**

    If :math:`g(x, y) = g_x(x) + g_y(y)`, the cut becomes

    .. math::
       \inf_{y \in Y} \{ \bar{\mu}^T (g_x(x) + g_y(y)) \} \leq 0.

    Moving the term involving only :math:`x` outside the infimum, we get

    .. math::
       \bar{\mu}^T g_x(x) + \inf_{y \in Y} \{ \bar{\mu}^T g_y(y) \} \leq 0.

    **2. Linearity in x**

    If we further assume :math:`g_x(x) = A x`, the cut simplifies to a linear inequality

    .. math:: \bar{\mu}^T A x + K'(\bar{\mu}) \leq 0, \quad \text{[Feasibility Cut]}
        :label: gbd_feas_cut_linear

    where :math:`K'(\bar{\mu}) = \inf_{y \in Y} \{ \bar{\mu}^T g_y(y) \}` is a constant that can be computed separately
    using unconstrained optimization methods over :math:`y`.

.. admonition:: Obtaining the Farkas Multiplier :math:`\bar{\mu}`
    :class: note

    For a general convex Non-Linear Programming subproblem, you can solve an auxiliary "feasibility-seeking" problem
    to find :math:`\bar{\mu}`. A common approach is to introduce slack variables and minimize their sum.

    .. math::
       \begin{aligned}
       \min_{y, s} \quad & \sum_i s_i \\
       \text{s.t.} \quad & g_i(\bar{x}, y) \leq s_i, \quad \forall i \\
                         & s_i \geq 0, \quad \forall i \\
                         & y \in Y
       \end{aligned}

    If the original subproblem is infeasible, the optimal objective of this auxiliary problem will be positive.
    The optimal Lagrange multipliers associated with the constraints :math:`g_i(\bar{x}, y) \leq s_i` are
    the components of the Farkas multiplier vector :math:`\bar{\mu}`.

.. tip::

    When the **linearly separable** condition is satisfied,
    and we have a **black-box nonlinear solver** that can provide a :math:`\bar{\mu}`
    for infeasible convex Non-Linear Programming problems,
    we can solve :math:`\min_{y \in Y} \{ \bar{\mu}^T g_y(y) \}`
    to compute :math:`K'(\bar{\mu})` and implement :eq:`gbd_feas_cut_linear`.

.. admonition:: Transforming to Classical Benders Cut
    :class: note

    **When the subproblem is a Linear Programming problem, the generalized feasibility cut simplifies to the classical Benders feasibility cut.**

    Consider a subproblem with constraints :math:`Dy \geq b - Ax`, which in the format :math:`g(x,y) \leq 0`
    is :math:`b - Ax - Dy \leq 0`.
    The generalized cut :eq:`gbd_feas_cut` is :math:`\bar{\mu}^T (b - Ax) + \inf_{y \geq 0} \{ -\bar{\mu}^T Dy \} \leq 0`.
    The key is to show that :math:`\inf_{y \geq 0} \{ -\bar{\mu}^T Dy \} = 0`.

    The Farkas multiplier :math:`\bar{\mu}` is an extreme ray from the dual of the subproblem,
    satisfying :math:`D^T \bar{\mu} \leq 0` and :math:`\bar{\mu} \geq 0`.
    From :math:`D^T \bar{\mu} \leq 0`, we get :math:`\bar{\mu}^T D \leq 0`.
    Since :math:`y \geq 0`, the term :math:`\bar{\mu}^T D y` is always non-positive.
    Therefore, :math:`-\bar{\mu}^T D y` is always non-negative.
    The infimum of a non-negative expression that can be zero (e.g., at :math:`y=0`) is zero.

    This reduces the generalized cut to :math:`\bar{\mu}^T (b - Ax) \leq 0`,
    which is the feasibility cut in the :doc:`classical`.

Algorithm
--------------------------------------------

The algorithm is an iterative process that alternates between solving the master problem, solving the subproblem,
and adding generalized Benders cuts to the master problem based on the subproblem's results.

#. **Initialization**

   *   Initialize a lower bound :math:`LB = -\infty` and an upper bound :math:`UB = +\infty`.
   *   Add any initial cuts to the master problem if available. Often, the algorithm starts with no cuts.
   *   Set the iteration counter :math:`k = 1`.

#. **Step 1: Solve the master problem**

   *   Solve the current master problem to get a solution :math:`(\bar{x}_k, \bar{\eta}_k)`.
   *   The objective value of the master problem, :math:`\bar{\eta}_k`, is a valid lower bound on
       the optimal solution of the original problem. Update :math:`LB = \max(LB, \bar{\eta}_k)`.

#. **Step 2: Check for convergence**

   *   If :math:`UB - LB \leq \epsilon` (where :math:`\epsilon` is a small tolerance), then **STOP**.
       The optimal solution has been found within the desired tolerance.
       The best solution found so far that yielded a feasible subproblem is the optimal solution.

#. **Step 3: Solve the subproblem**

   *   Using the fixed value :math:`\bar{x}_k` from the master problem, solve the convex Non-Linear Programming subproblem.

#. **Step 4: Generate and add a cut**

   *   **Case A: Subproblem is feasible.**

        *   Obtain the optimal subproblem solution :math:`\bar{y}_k` and the corresponding optimal Lagrange multipliers :math:`\bar{\lambda}_k`.
        *   The objective value for this feasible solution is :math:`f(\bar{x}_k, \bar{y}_k)`.
        *   Update the upper bound by :math:`UB = \min(UB, f(\bar{x}_k, \bar{y}_k))`.
        *   Add a **generalized optimality cut** to the master problem for lower bounding :math:`\eta`.

   .. caution::

        *   For :math:`-\infty < \eta < +\infty` introduced in the master problem for optimality cuts,
            :math:`-\infty` should be replaced with a sufficiently large negative number
            that remains as small as possible to ensure validity, to avoid numerical issues in practice.
        *   In BendersLib, :math:`-\infty` is provided as a customizable parameter :attr:`BendersParams.theta_lb`;
            :math:`+\infty` is set to solvers' default upper bound for unbounded variables.

   *   **Case B: Subproblem is infeasible.**

        *   Find a Farkas multiplier (or extreme ray) :math:`\bar{\mu}_k` and add a **generalized feasibility cut** to the master problem.


#. **Step 5: Loop**

   *   Increment :math:`k = k + 1` and go back to **Step 1**.

Given the set of complicating variables, the generalized Benders Decomposition method has a standard way to
formulate the master problem, subproblem, and Benders cuts.
Therefore, these procedures can be automated, and users only need to provide the original problem
and specify which variables are complicating variables.

.. seealso::

    - See :doc:`classical` for basic concepts of Benders decomposition.
    - An in-depth introduction to `GBD theory <https://mp.weixin.qq.com/s/cmxRNhrlIzEiJi2PTtUOOA>`_ (in Chinese).
    - **Papers using GBD**: facility location [#]_; budgeting [#]_; inventory management [#]_.
    - BendersLib's implementation of optimality and feasibility cuts: :class:`GeneralizedOC` and :class:`GeneralizedFC`.
    - BendersLib's implementation of the Benders method: :class:`GeneralizedBenders`.
    - **Examples**: :doc:`../examples/basic/gbd`, and more (:doc:`benders: generalized <../_tags/benders-generalized>`).

References
--------------------------------------------

.. [#] Geoffrion, A. M. (1972). Generalized Benders Decomposition. Journal of Optimization Theory and Applications, 10(4), 237–260. https://doi.org/10.1007/BF00934810
.. [#] Fischetti, M., Ljubić, I., & Sinnl, M. (2017). Redesigning benders decomposition for large-scale facility location. Management Science, 63(7), 2146–2162. https://doi.org/10.1287/mnsc.2016.2461
.. [#] Keshvari Fard, M., Ljubić, I., & Papier, F. (2022). Budgeting in international humanitarian organizations. Manufacturing & Service Operations Management, 24(3), 1261–1885. https://doi.org/10.1287/msom.2021.1016
.. [#] Guo, P., & Zhu, J. (2025). Coordinating International Humanitarian Inventory by Stochastic Dual Dynamic Programming. Naval Research Logistics (NRL). https://doi.org/10.1002/nav.70030

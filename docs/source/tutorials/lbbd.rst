.. _lbbd:

Logic-based Benders Decomposition
============================================

.. currentmodule:: benderslib

.. role:: raw-latex(raw)
   :format: latex

.. default-role:: raw-latex

The Logic-based Benders Decomposition (LBBD) [1]_ is a powerful generalization of the Benders Decomposition method.
While classical Benders decomposition requires the subproblem to be LP and generalized Benders requires convexity,
LBBD extends the framework to handle subproblems of any kind, including non-convex programming,
Constraint Programming (CP), or problem-specific algorithms.
The theory and its applications are detailed extensively in Hooker's books [2]_ [3]_.
The core idea is to replace the concept of LP duality with *inference duality*.
Instead of relying on a dual LP to generate cuts, LBBD uses a logical inference or a "proof" from the subproblem solver
to derive *logic-based Benders cuts*.

Inference Duality
--------------------------------------------

Consider a general optimization problem

.. math::

    \min_{x} \{ f(x) \mid \mathcal{C}(x), x \in \mathcal{D} \}

where :math:`f(x)` is the objective function, :math:`\mathcal{C}(x)` is the set of constraints,
and :math:`\mathcal{D}` is the domain of the variables.
The **inference dual** [1]_ [2]_ [3]_ of this problem finds the best possible lower bound :math:`\beta`
on the objective value that can be inferred from the constraints.

.. math::

    \max_{\beta, P} \{ \beta \mid (\mathcal{C}(x), x \in \mathcal{D}) \vdash_P (f(x) \geq \beta) \}

The notation :math:`S \vdash_P L` means that the statement :math:`L` can be inferred from the set of premises :math:`S`
using a proof :math:`P` from a specific proof system.
The inference dual seeks the tightest lower bound :math:`\beta` that can be deduced.
A key result is that when we assume :math:`\infty` objective values for infeasible problems and :math:`-\infty` for unbounded ones,
**strong duality** holds [1]_: the optimal value of the original problem is equal to the optimal value of its inference dual.

LBBD Reformulation
--------------------------------------------

LBBD addresses problems with the following structure, where variables are partitioned into
master problem variables :math:`x` and subproblem variables :math:`y`.

.. math::

   \begin{aligned}
   \min_{x, y} \quad & f(x, y) \\
   \text{s.t.} \quad & \mathcal{C}(x, y) \\
                     & \mathcal{C}'(x) \\
                     & x \in \mathcal{D}_x \\
                     & y \in \mathcal{D}_y
   \end{aligned}

When the master problem proposes a solution :math:`\bar{x}`, the following **subproblem** is solved.

.. math::

   \begin{aligned}
   \min_{y} \quad & f(\bar{x}, y) \\
   \text{s.t.} \quad & \mathcal{C}(\bar{x}, y) \\
                     & y \in \mathcal{D}_y
   \end{aligned}

The **inference dual** seeks the tightest possible lower bound :math:`\beta` on the objective value
that can be logically inferred from the subproblem's constraints.
For a given :math:`\bar{x}`, it is formulated as follows.

.. math::

   \begin{aligned}
   \max_{\beta, P} \{\beta \mid (\mathcal{C}(\bar{x}, y), y \in \mathcal{D}_y) \vdash_P (f(\bar{x}, y) \geq \beta)\}
   \end{aligned}

Here, :math:`\vdash_P` indicates that the conclusion :math:`f(\bar{x}, y) \geq \beta` is derivable from
the subproblem constraints using a proof :math:`P` from a specific inference system.
Solving this dual yields an optimal lower bound :math:`\beta^*`, representing the strongest conclusion
we can draw about the cost associated with the master decision :math:`\bar{x}`.

The Benders master problem is then formulated to find the best master variables :math:`x` while respecting
the information learned from previous iterations.
Let :math:`\bar{x}^k` be the master solution at iteration :math:`k`,
and let :math:`B_{\bar{x}^k}(x)` be the function representing the lower bound generated from that iteration's subproblem.
The **master problem** at iteration :math:`K` becomes follows.

.. math::

   \begin{aligned}
   \min_{x, z} \quad & z \\
   \text{s.t.} \quad & \mathcal{C}'(x) \\
                     & z \geq B_{\bar{x}^k}(x), \quad \forall k = 1, \dots, K \\
                     & x \in \mathcal{D}_x
   \end{aligned}

The constraints :math:`z \geq B_{\bar{x}^k}(x)` are the **logic-based Benders cuts**.

.. note::
    Here we use :math:`z` to represent the objective function of the master problem in consistency with Hooker's notation [3]_.
    However, The master problem objective can also be expressed using only terms with :math:`x` in :math:`f(x, y)`,
    plus an estimator variable representing the subproblem's contribution, similar to other Benders methods in this tutorial.
    BendersLib uses the latter internally.

Logic-based Benders Cuts
--------------------------------------------

A key challenge in implementing LBBD is translating the general cut :math:`z \geq B_{\bar{x}^k}(x)` from
the master problem into a concrete mathematical constraint.
Unlike the standard cuts in :doc:`../tutorials/classical`, :doc:`../tutorials/cbd`, :doc:`../tutorials/lshaped`,
or :doc:`../tutorials/ilshaped`, logic-based Benders cuts are problem-specific.

.. note::
    Hooker's Book (Chapter 3) [3]_ summarized various forms of logic-based Benders cuts,
    including no-good cuts, analytical cuts, etc.

.. admonition:: Example
    :class: seealso

    When the expression :math:`B_{\bar{x}^k}(x)` in the original cut :math:`z \geq B_{\bar{x}^k}(x)`
    is replaced by :math:`\beta_k = B_{\bar{x}^k}(\bar{x}^k)`, the cut takes the following form.

    .. math::

       (x = \bar{x}^k) \Rightarrow (z \geq \beta_k)

    This is essentially the :class:`CombinatorialOC` in :doc:`../tutorials/cbd` and :doc:`../tutorials/ilshaped`.
    It states that if the master problem again chooses the solution :math:`\bar{x}^k`,
    then the objective :math:`z` must be at least the lower bound :math:`\beta_k` that was inferred for this solution.
    This logical form can be directly translated into
    :abbr:`indicator constraints (where a constraint is activated only when a binary variable takes a certain value)`,
    which are supported by many modern mathematical programming solvers.
    It can be linearized using big-M formulations, which has been introduced
    in :doc:`../tutorials/cbd` and :doc:`../tutorials/ilshaped`.

    :math:`(x = \bar{x}^k) \Rightarrow (z \geq \beta_k)` is presented here for illustrative purposes.
    It can be weaker than :math:`z \geq B_{\bar{x}^k}(x)`
    because it only enforces the bound when :math:`x` exactly matches :math:`\bar{x}^k`,
    providing no gradient information for other values of :math:`x`.

Depending on the subproblem outcome for a given :math:`\bar{x}^k`, the cut conveys different information.

*   **When the subproblem is feasible**,
    an **optimality cut** of the form :math:`z \geq B_{\bar{x}^k}(x)` is added.
    This informs the master problem of the cost consequence of repeating the decision :math:`\bar{x}^k`.

*   **When the subproblem is infeasible**,
    the proof of infeasibility identifies a subset of decisions in :math:`\bar{x}^k` that make subproblem infeasible.
    A **feasibility cut** (e.g., no-good cut) is generated to forbid this specific combination of critical decisions in future iterations.

The LBBD framework is particularly well-suited for problems involving integer variables in both the master and subproblems.
When applying LBBD to stochastic programming problems, cuts are generated for each discrete scenario or aggregated for all scenarios,
similar to :doc:`../tutorials/lshaped` and :doc:`../tutorials/ilshaped`.

.. note::

    :doc:`../tutorials/cbd` is a special case of LBBD.
    In CBD, the subproblems are typically MILPs, and the "proofs" correspond to an IIS (for feasibility cuts)
    or the optimal objective value itself (for optimality cuts), which are then formulated using
    :class:`NoGoodFC` and :class:`CombinatorialOC`, respectively.
    LBBD generalizes this by formalizing the use of any valid deductive system to create problem-specific cuts,
    enabling the handling of a broader class of subproblems beyond MILPs.

Algorithm
--------------------------------------------
The LBBD algorithm follows the same iterative master-subproblem scheme as other Benders methods.

#. **Initialization**

   *   Initialize a lower bound :math:`LB = -\infty` and an upper bound :math:`UB = +\infty`.
   *   The master problem starts with constraints :math:`\mathcal{C}'(x)` and domain :math:`x \in \mathcal{D}_x`.
   *   Set the iteration counter :math:`k = 1`.

#. **Step 1: Solve the master problem**

   *   Solve the current master problem to obtain a solution :math:`(\bar{x}_k, \bar{z}_k)`.
   *   Update the lower bound: :math:`LB = \max(LB, \bar{z}_k)`.

#. **Step 2: Check for convergence**

   *   If :math:`UB - LB \leq \epsilon` (for a small tolerance :math:`\epsilon`), **STOP**. The optimal solution has been found.

#. **Step 3: Solve the subproblem**

   *   Fix :math:`x = \bar{x}_k` and solve the subproblem.

   .. note::
       The subproblem can be solved using any appropriate method, including (**but not limited to**)
       MILP solvers, CP solvers, or custom/problem-specific algorithms
       (e.g., network flow algorithms, shortest path algorithms, etc.).

#. **Step 4: Generate and add a cut**

   *   Analyze the proof from the subproblem to generate a logic-based Benders cut.
   *   If the subproblem is **infeasible**, the cut excludes the infeasible master solution.
   *   If the subproblem is **feasible** with cost :math:`z^*_k`, update the upper bound :math:`UB = \min(UB, z^*_k)`
       and add a cut enforcing that the cost must be at least :math:`z^*_k` if the master decisions are repeated.
   *   Add the generated cut to the master problem.

#. **Step 5: Loop**

   *   Increment :math:`k = k + 1` and go back to **Step 1**.

The main challenge in applying LBBD is to design a problem-specific cut generation procedure that can extract a strong, concise logical explanation from the subproblem solution process.

.. seealso::

    * Hooker's book [3]_ that comprehensively covers LBBD theory and applications.
    * LBBD for planning and scheduling with specific examples and logic-based Benders cuts [4]_.
    * LBBD for stochastic optimization with specific examples and logic-based Benders cuts [5]_.
    * **Examples**: :doc:`../examples/advanced/lbbd`, :doc:`../examples/advanced/lbbd_sp`, :doc:`../examples/advanced/lbbd_lshaped`, :doc:`../examples/benchmarks/lbbd_location`, and more (:doc:`benders: lbbd <../_tags/benders-lbbd>`).

References
----------

.. [1] Hooker, J. N., & Ottosson, G. (2003). Logic-based Benders decomposition. Mathematical Programming, 96(1), 33–60. https://doi.org/10.1007/s10107-003-0375-9
.. [2] Hooker, J. N. (2019). Logic-based Benders decomposition for large-scale optimization. In J. M. Velásquez-Bermúdez, M. Khakifirooz, & M. Fathi (Eds.), Large Scale Optimization in Supply Chains and Smart Manufacturing: Theory and Applications (pp. 1–26). Springer International Publishing. https://doi.org/10.1007/978-3-030-22788-3_1
.. [3] Hooker, J. (2024). Logic-Based Benders Decomposition: Theory and Applications. Springer International Publishing. https://doi.org/10.1007/978-3-031-45039-6
.. [4] Hooker, J. N. (2007). Planning and scheduling by logic-based Benders decomposition. Operations Research, 55(3), 588–602. https://doi.org/10.1287/opre.1060.0371
.. [5] Elçi, Ö., & Hooker, J. (2022). Stochastic planning and scheduling with logic-based Benders decomposition. INFORMS Journal on Computing, 34(5), 2383–2865. https://doi.org/10.1287/ijoc.2022.1184

Solver Interfaces
===========================================

.. currentmodule:: benderslib

Supported Solvers
-------------------------------------------

.. attention::

   BendersLib will **NOT** install any solver to your environment automatically.
   You need to :ref:`install the solvers <manual_installing_solver>` separately based on your needs.

BendersLib supports the following solvers.
The features listed in the table are essential for Benders decomposition.
A Benders decomposition variant usually require one or two features to work properly.

* **Dual**:
  The solver can provide dual values of constraints. This is essential for generating *classical optimality cuts*.
  This feature can be required by :doc:`../tutorials/classical` and :doc:`../tutorials/lshaped` implemented
  with :class:`ClassicalBenders` and :class:`LShaped`, respectively, if the user wants to add optimality cuts.
* **Farkas**:
  The solver can provide a Farkas certificate of infeasibility (an extreme ray of the dual).
  This is used to generate *classical feasibility cuts*.
  This feature can be required by :doc:`../tutorials/classical` and :doc:`../tutorials/lshaped` implemented
  with :class:`ClassicalBenders` and :class:`LShaped`, respectively, if the user wants to add feasibility cuts.
* **IIS**:
  The solver can find an Irreducible Inconsistent Subsystem (IIS).
  This helps building stronger *no-good cuts*.
  This feature usually works with :doc:`../tutorials/cbd` and :doc:`../tutorials/lbbd` implemented
  with :class:`CombinatorialBenders` and :class:`LogicBasedBenders`, respectively, if the user wants to add no-good
  feasibility cuts.
* **BnC**:
  The solver supports :ref:`branch-and-check <enhance_branch_and_check>`, or branch-and-Benders-cut,
  a modern implementation of Benders decomposition
  that integrates cut generation into the branch-and-bound algorithm of the master problem solver.
  Instead of solving the master problem to optimality at each iteration, it checks the feasibility
  and optimality of the current solution at each node of the branch-and-bound tree and adds cuts as needed.
  This requires the master problem solver to support callback functions for adding cuts during the
  branch-and-bound process.

.. admonition:: Examples
    :class: seealso

    - See :doc:`../examples/solvers/index` for example code using different solvers with BendersLib.
    - See :doc:`../examples/iis/index` for example code of computing IIS with different solvers.

.. list-table:: Supported Solvers' Features
    :widths: auto
    :header-rows: 1
    :name: solver-table

    * - Solver
      - Class
      - Doc
      - Dual
      - Farkas
      - IIS
      - BnC
      - License
    * - **COPT**
      - :class:`~.solvers.Copt`
      - `Doc <https://guide.coap.online/copt/en-doc/>`__
      - ✅
      - ✅
      - ✅
      - ✅
      - Commercial
    * - **CPLEX**
      - :class:`~.solvers.Cplex`
      - `Doc <https://www.ibm.com/docs/en/icos/22.1.2?topic=optimizers-cplex-python-api-reference-manual>`__
      - ✅
      - ✅
      - ✅
      - ✅
      - Commercial
    * - **CP Optimizer**
      - :class:`~.solvers.CplexCP`
      - `Doc <https://ibmdecisionoptimization.github.io/docplex-doc/cp/docplex.cp.model.py.html>`__
      - ❌
      - ❌
      - ✅
      - ❌
      - Commercial
    * - **Gurobi**
      - :class:`~.solvers.Gurobi`
      - `Doc <https://docs.gurobi.com>`__
      - ✅
      - ✅
      - ✅
      - ✅
      - Commercial
    * - **OR-Tools** [1]_
      - :class:`~.solvers.Ortools`
      - `Doc <https://developers.google.com/optimization/cp>`__
      - ❌
      - ❌
      - ✅
      - ❌
      - Open-source
    * - **SCIP**
      - :class:`~.solvers.Scip`
      - `Doc <https://pyscipopt.readthedocs.io>`__
      - 🟨 [2]_
      - ✅
      - ✅
      - ✅
      - Open-source
    * - **Pyomo** [3]_:
      - :class:`~.solvers.Pyomo`
      - `Doc <https://pyomo.readthedocs.io>`__
      - \-
      - \-
      - [4]_
      - \-
      - Open-source
    * - CBC
      - ``'cbc'``
      - `Doc <https://www.coin-or.org/Cbc/cbcuserguide.html>`__
      - ✅
      - ❌
      - ✅
      - ❌
      - Open-source
    * - CPLEX
      - ``'cplex'``, ``'cplex_direct'``
      - `Doc <https://www.ibm.com/docs/en/icos/22.1.2?topic=optimizers-users-manual-cplex>`__
      - ✅
      - ❌
      - ✅
      - ❌
      - Commercial
    * -
      - ``'cplex_persistent'``
      - `Doc <https://www.ibm.com/docs/en/icos/22.1.2?topic=optimizers-users-manual-cplex>`__
      - ✅
      - ❌
      - ✅
      - ❌
      - Commercial
    * - GLPK
      - ``'glpk'``
      - `Doc <https://www.gnu.org/software/glpk/>`__
      - ✅
      - ❌
      - ✅
      - ❌
      - Open-source
    * - Gurobi
      - ``'gurobi'``, ``'gurobi_direct'``
      - `Doc <https://docs.gurobi.com>`__
      - ✅
      - ❌
      - ✅
      - ❌
      - Commercial
    * -
      - ``'gurobi_persistent'``
      - `Doc <https://docs.gurobi.com>`__
      - ✅
      - ✅
      - ✅
      - ❌
      - Commercial
    * - HiGHS
      - ``'highs'``
      - `Doc <https://highs.dev>`__
      - ✅
      - ❌
      - ❌
      - ❌
      - Open-source
    * - MOSEK
      - ``'mosek'``, ``'mosek_direct'``
      - `Doc <https://docs.mosek.com>`__
      - ✅
      - ❌
      - ✅
      - ❌
      - Commercial
    * - SCIP
      - ``'scip'``
      - `Doc <https://www.scipopt.org>`__
      - ❌ [2]_
      - ❌
      - ✅
      - ❌
      - Open-source
    * - Xpress
      - ``'xpress'``, ``'xpress_direct'``
      - `Doc <https://www.fico.com/en/products/fico-xpress-optimization>`__
      - ✅
      - ❌
      - ✅
      - ❌
      - Commercial
    * -
      - ``'xpress_persisitent'``
      - `Doc <https://www.fico.com/en/products/fico-xpress-optimization>`__
      - ✅
      - ❌
      - ✅
      - ❌
      - Commercial

.. [1] *Here we only use the CP-SAT solver provided by OR-Tools for Constraint Programming (CP).*
.. [2] *SCIP may return incorrect dual values*
       (*see* `this discussion <https://stackoverflow.com/a/79562415/6729710>`_ *and*
       `documentation <https://pyscipopt.readthedocs.io/en/latest/tutorials/constypes.html#constraint-information>`_;
       *and* `this issue <https://github.com/scipopt/PySCIPOpt/issues/228>`_).
       *All-zero dual values are returned when using SCIP in Pyomo.*
.. [3] *Pyomo is a modeling language. Supported solvers must be installed separately, see*
       :ref:`solver-installation-table` *(by BendersLib),*
       `installation instruction <https://pyomo.readthedocs.io/en/stable/getting_started/solvers.html>`_ *(by Pyomo),*
       *and* `supported solvers <https://github.com/Pyomo/pyomo/tree/main/pyomo/solvers/plugins/solvers>`_.
.. [4] *Using* `Minimal Intractable System (MIS) Finder <https://pyomo.readthedocs.io/en/stable/api/pyomo.contrib.iis.mis.html>`_.

.. Nonlinear Solvers: IPOPT, Minotaur, Baron, KNITRO
.. CP Solvers: Xpress Kalis, python-constraint, Z3, via MiniZinc (https://docs.minizinc.dev/en/stable/solvers.html)
.. Modeling Languages: MiniZinc, PuLP, CVXPY, GEKKO, GAMS, AMPL

.. https://news.ycombinator.com/item?id=45671176

.. Solver List by Pyomo:        https://pyomo.readthedocs.io/en/stable/getting_started/solvers.html
.. Solver List by AMPL:         https://dev.ampl.com/solvers/index.html
.. Solver List by JuMP:         https://jump.dev/JuMP.jl/stable/installation/#Supported-solvers
.. Solver List by YALMIP:       https://yalmip.github.io/allsolvers/
.. Solver List by PySCIPOpt:    https://pyscipopt.readthedocs.io/en/latest/solvers.html
.. Solver List by CBC:          https://github.com/coin-or/Cbc
.. Solver List by AIMMS:        https://documentation.aimms.com/platform/solvers/solvers.html

These solvers can be categorized into two groups: Mathematical Programming solvers (most of the solvers supported)
and Constraint Programming solvers (:class:`~.solvers.CplexCP` and :class:`~.solvers.Ortools`),
which are two different paradigms for solving optimization problems.
They have distinct approaches and are suited for different types of problems.
A wise choice between the two can lead to more efficient problem-solving.

.. list-table:: Mathematical Programming vs Constraint Programming
   :widths: 25 37 38
   :header-rows: 1

   * - Feature
     - Mathematical Programming
     - Constraint Programming
   * - **Origin**
     - Operations Research (OR)
     - Artificial Intelligence (AI)
   * - **Core Idea**
     - Optimize a specific objective function subject to a set of constraints.
     - Find a feasible solution that satisfies all constraints, without necessarily having an objective function.
   * - **Typical Techniques**
     - Simplex method, interior-point methods.
     - Backtracking, constraint propagation, and local search.
   * - **Best Suited For**
     - Problems with quantitative variables and linear/nonlinear relationships.
     - Problems with combinatorial structures and discrete variables.

There are many successful attempts that **combing both paradigms**.
Specifically in :doc:`../tutorials/cbd` and :doc:`../tutorials/lbbd`,
master problems are often modeled using Mathematical Programming,
while subproblems can be modeled using Constraint Programming to leverage its strengths in handling combinatorial constraints.

**Using a solver not listed here? No worries!**
See the next section on how to create a custom solver interface,
and see :ref:`Custom Subproblem <manual_custom_sub>` for even simpler ways to use custom solvers for subproblems.

====

.. _manual_custom_solver_interface:

Customization
-------------------------------------------

BendersLib is designed to be extensible, allowing you to integrate solvers that are not natively supported.
This is achieved by creating a custom solver interface.

To add a new solver, you need to create a class that inherits from :class:`SolverBase`
(for Mathematical Programming, or :class:`SolverCPBase` for Constraint Programming).
This base class serves as a template for all solver interfaces in BendersLib.
The :class:`SolverBase` is an `Abstract Base Class (ABC) <https://docs.python.org/3/library/abc.html>`_,
a feature from Python.
ABCs are used to define interfaces,
meaning a concrete class that inherits from an ABC must implement all of its
`abstract methods <https://docs.python.org/3/library/abc.html#abc.abstractmethod>`_.
This ensures that every solver interface in BendersLib provides a consistent set of functionalities.
When you create your custom solver class,
you must inherit from :class:`SolverBase` and provide implementations for all methods decorated with ``@abstractmethod``,
and define all attributes defined in :class:`SolverBase`.

While :class:`SolverBase` defines several abstract methods that you must implement,
two methods, :meth:`~SolverBase.make_master_problem` and :meth:`~SolverBase.make_sub_problem`,
have special considerations.
These methods are essential for the :class:`AnnotatedBenders` class,
which automates the decomposition process.
If you do not intend to use :class:`AnnotatedBenders`,
you might not need to implement the full logic for these methods.
However, for a solver interface to be considered for contribution to the official BendersLib repository,
a complete and functional implementation of these methods is required to ensure full compatibility with all library features.

To see a practical implementation, you can refer to the source code of the built-in solver interfaces,
such as :class:`~.solvers.Gurobi`.
Examining how it inherits from :class:`SolverBase` and implements the required methods will provide a clear
and effective template for creating your own custom solver.

**Contributing solver interfaces to BendersLib is welcome!**
See :doc:`contribution` for how to contribute your custom solver interface to the official repository.

====

Attributes & Methods
-------------------------------------------

Below are the attributes and methods of the base solver interfaces :class:`SolverBase` (Mathematical Programming)
and :class:`SolverCPBase` (Constraint Programming).
Any built-in solver interface is inherited from one of them, with the attributes and methods properly implemented.
Adding a new solver interface requires implementing these attributes and methods,
especially the `abstract methods <https://docs.python.org/3/library/abc.html#abc.abstractmethod>`_.
See :class:`SolverBase`  nd :class:`SolverCPBase` for the comprehensive API reference,
and :doc:`built-in solver interfaces <../api/solvers>` for examples.
Note that the solver interfaces are not designed to be used directly by end-users.
Use :class:`MasterProblem` and :class:`SubProblem` instead,
which internally utilize the solver interfaces to interact with the optimization solvers.

.. mermaid::
    :caption: Solver Interface Inheritance Diagram
    :align: center

    flowchart TB
        subgraph "Mathematical Programming"
            Gurobi
            Copt
            Pyomo
            Scip
            Cplex
        end

        subgraph "Constraint Programming"
            Ortools
            CplexCP
        end

        Gurobi -- inherits --> SolverBase
        Copt -- inherits --> SolverBase
        Pyomo -- inherits --> SolverBase
        Scip -- inherits --> SolverBase
        Cplex -- inherits --> SolverBase
        Ortools -- inherits --> SolverCPBase
        CplexCP -- inherits --> SolverCPBase

.. rubric:: :class:`SolverBase` - Attributes

.. autosummary::
   :nosignatures:

   ~SolverBase.model
   ~SolverBase.status

.. tip::

    More attributes can be accessed via :attr:`~SolverBase.model`, which is the underlying solver model instance.

.. rubric:: :class:`SolverBase` - Methods

.. autosummary::
   :nosignatures:

   ~SolverBase.add_estimators
   ~SolverBase.fix_vars
   ~SolverBase.unfix_vars
   ~SolverBase.get_var_values
   ~SolverBase.get_var_coefs
   ~SolverBase.get_rhs
   ~SolverBase.get_dual_values
   ~SolverBase.get_extreme_ray
   ~SolverBase.get_obj
   ~SolverBase.add_cut
   ~SolverBase.remove_cut
   ~SolverBase.solve
   ~SolverBase.compute_iis
   ~SolverBase.make_master_problem
   ~SolverBase.make_sub_problem

.. rubric:: :class:`SolverCPBase` - Attributes

.. autosummary::
   :nosignatures:

   ~SolverCPBase.model
   ~SolverCPBase.status

.. rubric:: :class:`SolverCPBase` - Methods

.. autosummary::
   :nosignatures:

   ~SolverCPBase.fix_vars
   ~SolverCPBase.unfix_vars
   ~SolverCPBase.get_var_values
   ~SolverCPBase.get_obj
   ~SolverCPBase.compute_iis
   ~SolverCPBase.solve

How-To Guides
=============================================================

.. currentmodule:: benderslib

.. contents::
   :local:
   :depth: 1
   :class: this-will-duplicate-information-and-it-is-still-useful-here

*To be added (common issues will be summarized here)...*

------

How to access to attributes not listed in the API reference?
--------------------------------------------------------------

Sometimes, users may want to access to certain attributes of the underlying solver model
that are not directly exposed in the BendersLib API reference.
In such cases, users can utilize the attribute :attr:`ProblemBase.model`
(the base class for :class:`MasterProblem` and :class:`SubProblem`)
to access the underlying solver model directly.
For example, if you are using :class:`~.solvers.Gurobi`, you can access the Gurobi model as follows.

.. code-block:: python

    from benderslib import AnnotatedBenders, ClassicalBenders
    from benderslib.solvers import Gurobi
    from gurobipy import Model, GRB


    # Create a standard Gurobi model
    model = Model()
    x = model.addVar(name="x", vtype=GRB.INTEGER)
    y = model.addVar(name="y", vtype=GRB.CONTINUOUS)
    model.addConstr(x + y >= 15)
    model.addConstr(2 * x + 5 * y >= 30)
    model.setObjective(3 * x + 4 * y)
    model.update()

    # Complicating variable
    complicating_vars = ["x"]

    # Create and solve using Benders decomposition
    benders = AnnotatedBenders(
        model,
        solver=Gurobi,
        complicating_vars=complicating_vars,
        benders=ClassicalBenders
    )
    benders.solve()

    # Access the underlying Gurobi model
    gurobi_model = benders.master_problem.model
    print(f"Gurobi Model Status: {gurobi_model.Status}")

.. seealso::

    Refer to the :ref:`documentation of the specific solver <solver-table>` for more available attributes.

How to build master/sub problems from a monolithic model?
--------------------------------------------------------------

BendersLib offers two ways to decompose a monolithic optimization model into master and sub problems.
You can either use the :meth:`AnnotatedBenders.decompose` method,
or the solver-specific methods like :meth:`~.SolverBase.make_master_problem` and :meth:`~.SolverBase.make_sub_problem`.
The following example demonstrates both approaches.

.. code-block:: python

    from benderslib import AnnotatedBenders, MasterProblem, SubProblem
    from gurobipy import Model, GRB

    # Use other solver interfaces (e.g., Copt, etc) as needed
    from benderslib.solvers import Gurobi


    # Create a standard Gurobi model
    model = Model()
    x = model.addVar(name="x", vtype=GRB.INTEGER)
    y = model.addVar(name="y", vtype=GRB.CONTINUOUS)
    model.addConstr(x + y >= 15)
    model.addConstr(2 * x + 5 * y >= 30)
    model.setObjective(3 * x + 4 * y)
    model.update()

    # Define master variables for decomposition
    master_vars = ["x"]

    # Approach 1:
    master_problem, sub_problem = AnnotatedBenders.decompose(
        original_problem=model,
        solver=Gurobi,
        master_vars=master_vars,
        # You can also get the raw solver models
        # solver_model=True
    )

    # Approach 2:
    master_model_manual = Gurobi.make_master_problem(model, master_vars)
    sub_model_manual = Gurobi.make_sub_problem(model, master_vars)

    # These models can then be used to create MasterProblem and SubProblem instances
    master_problem_manual = MasterProblem(Gurobi(master_model_manual))
    sub_problem_manual = SubProblem(Gurobi(sub_model_manual))

How to start from standard mathematical programming files?
--------------------------------------------------------------

BendersLib can be used with models created from standard mathematical programming files (e.g., ``.mps``, ``.lp``).
You can use the functions of the external solver to read the model file,
and then use the :class:`AnnotatedBenders` class or the :meth:`~.SolverBase.make_master_problem`
and :meth:`~.SolverBase.make_sub_problem` methods to perform the decomposition.
The supported file formats depend on the underlying solver being used.
The following example shows how to read a ``.lp`` file using Gurobi and then apply Benders decomposition.

.. code-block:: python

    from gurobipy import read
    from benderslib.solvers import Gurobi
    from benderslib import AnnotatedBenders, ClassicalBenders


    # Read model from file
    model = read("model.lp")

    # The content of ``model.lp``:
    #
    # Minimize
    #   3 x + 4 y
    # Subject To
    #   c1: x + y >= 15
    #   c2: 2 x + 5 y >= 30
    # Bounds
    #   x >= 0
    #   y >= 0
    # Generals
    #   x
    # End

    # Define complicating variables
    complicating_vars = ["x"]

    # Create and solve using Benders decomposition
    benders = AnnotatedBenders(
        model,
        solver=Gurobi,
        complicating_vars=complicating_vars,
        benders=ClassicalBenders
    )
    benders.solve()

    # We can also use the make_master_problem and make_sub_problem methods
    master_model = Gurobi.make_master_problem(model, complicating_vars)
    sub_model = Gurobi.make_sub_problem(model, complicating_vars)

How to convert models between solvers?
--------------------------------------------------------------

To move a mathematical programming model to a different solver, choose a file format
that both solvers support, such as ``.mps`` or ``.lp``.
Use the source solver's built-in writer to export the model and the target solver's
built-in reader to load it. The following example converts a Gurobi model to a SCIP model.

.. code-block:: python

    from gurobipy import Model as GurobiModel, GRB
    from pyscipopt import Model as ScipModel


    # Create and export a Gurobi model
    model = GurobiModel()
    x = model.addVar(name="x", vtype=GRB.INTEGER)
    y = model.addVar(name="y")
    model.addConstr(x + y >= 15)
    model.setObjective(3 * x + 4 * y)
    model.write("model.mps")

    # Read the model into SCIP
    scip_model = ScipModel()
    scip_model.readProblem("model.mps")

You can then use ``scip_model`` with the :class:`~.solvers.Scip` interface in BendersLib.
Pyomo has no built-in reader for importing LP or MPS files into a Pyomo model.
You can export a Pyomo model to ``.lp`` or ``.mps`` and load it into a solver that supports the format.

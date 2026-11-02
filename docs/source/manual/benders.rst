Benders Methods
===========================================

.. currentmodule:: benderslib

Create a Benders Decomposition Instance
-------------------------------------------

For most Benders decomposition methods, you need to provide :ref:`a master problem <manual_master_create>`,
:ref:`a subproblem <manual_sub_create>`, and a list of complicating variable names.
BendersLib will then build a Benders decomposition framework to your problem.

.. code-block:: python

    from benderslib import ClassicalBenders, MasterProblem, SubProblem

    # Assume master_problem and sub_problem are already defined
    master_problem: MasterProblem = ...
    sub_problem: SubProblem = ...
    complicating_vars: list[str] = ...

    # Create a Benders Decomposition instance
    benders_solver = ClassicalBenders(
        master_problem=master_problem,
        sub_problem=sub_problem,
        complicating_vars=complicating_vars
    )

Alternatively, you can create a Benders decomposition instance directly
from your models using the :meth:`~BendersSolver.from_models`
:abbr:`class method (a method bound to the class, not the instance)`.
This method is a convenient way to instantiate a Benders solver without manually
creating :class:`MasterProblem` and :class:`SubProblem` objects.

.. code-block:: python

    from benderslib import ClassicalBenders
    from benderslib.solvers import Gurobi

    # Assume master_model and sub_model are already defined
    master_model = ...
    sub_model = ...
    complicating_vars: list[str] = ...

    # Create a Benders Decomposition instance from models
    benders_solver = ClassicalBenders.from_models(
        master_model=master_model,
        master_solver=Gurobi,
        sub_model=sub_model,
        sub_solver=Gurobi,
        complicating_vars=complicating_vars
    )

BendersLib offers several built-in Benders decomposition methods, each designed for specific problem structures.
These methods are subclasses of :class:`BendersSolver` and come pre-configured with appropriate cut generators.
Each of the classes (except :class:`LogicBasedBenders` and :class:`OracleBenders`)
is a ready-to-use implementation of a Benders decomposition variant.

.. _manual_builtin_benders:

.. rubric:: Built-in Benders Decomposition Methods

.. autosummary::
   :nosignatures:

   ~ClassicalBenders
   ~CombinatorialBenders
   ~LShaped
   ~IntegerLShaped
   ~LogicBasedBenders
   ~OracleBenders
   ~GeneralizedBenders
   ~GeneLShaped

Options for Benders Decomposition
-------------------------------------------

These options are set after creating a Benders Decomposition instance,
but before calling the :meth:`BendersSolver.solve` method.
Please refer to :class:`BendersParams` for the available options to customize
the behavior of BendersLib's Benders Decomposition methods.

.. code-block:: python

    from benderslib import ClassicalBenders, BendersParams

    # Create Benders Decomposition instance
    benders_solver = ClassicalBenders(master_problem, sub_problem, complicating_vars)

    # Customize Benders parameters
    benders_solver.params.time_limit = 600  # Set time limit to 600 seconds

Alternatively, you can pass a :class:`BendersParams` instance as an argument when creating the Benders Decomposition instance.

.. code-block:: python

    from benderslib import ClassicalBenders, BendersParams

    # Customize Benders parameters
    params = BendersParams()
    params.time_limit = 600  # Set time limit to 600 seconds

    # Create Benders Decomposition instance with custom parameters
    benders_solver = ClassicalBenders(
        master_problem, sub_problem, complicating_vars,
        params=params
    )

Solve the Benders Decomposition Instance
-------------------------------------------

After creating and customizing a Benders Decomposition instance,
you can solve it using the :meth:`BendersSolver.solve` method.

.. code-block:: python

    # Solve the Benders Decomposition instance
    result = benders_solver.solve()

The output in the console will display the progress of the Benders Decomposition algorithm,
including iteration details and convergence information.

.. code-block:: console

    ====================================================================================
    BendersLib (v0.5.1, Apache-2.0, https://benders.dev) (C) 2021-2026 Peng-Hui Guo
    ------------------------------------------------------------------------------------
    Benders Decomposition:
     - Method:                  ClassicalBenders
     - Complicating Var. No.:   1 [Integer: 1, Binary: 0, Continuous: 0]
     - Optimality Cut:          ClassicalOCGen
     - Feasibility Cut:         ClassicalFCGen
    Master Problem:
     - Variable No.:            2 [Integer: 1, Binary: 0]
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
               1,         0.00,        60.00,        60.00,       100.00,         0.00
    ------------------------------------------------------------------------------------
    Benders Result:
      - Status:                  OPTIMAL
      - Incumbent:               45.0000
      - Bound:                   45.0000
      - Gap (abs.):              0.0000
      - Gap (rel.):              0.00%
      - Solutions No.:           2
      - Iteration No.:           2
      - Cuts No.:                1 [Optimality: 1, Feasibility: 0]
      - Solve Time (sec.):       0.01 [Master: 0.01, Sub: 0.00]
    ====================================================================================

The console output provides a summary of the Benders decomposition process, starting with a header displaying library and copyright information;
followed by problem information detailing the decomposition setup, including the method, complicating variables, and cut generators;
an iteration log tracking the lower and upper bounds, objective value, and runtime;
and a final results section summarizing the outcome with the solution status, incumbent value, and performance metrics.

Access Additional Statistics
-------------------------------------------

To access additional statistics after solving,
you can use the :attr:`BendersSolver.result` attribute, which contains various information about the solution process.
This attribute is an instance of the :class:`BendersResult` class.

.. code-block:: python

    # Access Benders result statistics
    print(f"Status: {benders_solver.result.status}")
    print(f"Objective: {benders_solver.result.obj}")
    print(f"Lower Bound: {benders_solver.result.lb}")
    print(f"Upper Bound: {benders_solver.result.ub}")
    print(f"Gap (abs.): {benders_solver.result.gap_abs}")
    print(f"Gap (rel.): {benders_solver.result.gap:.2%}")
    print(f"Number of Solutions: {benders_solver.result.n_sol}")
    print(f"Number of Iterations: {benders_solver.result.n_iter}")
    print(f"Number of Cuts: {benders_solver.result.n_cuts} (Opt: {benders_solver.result.n_opt_cuts}, Feas: {benders_solver.result.n_feas_cuts})")
    print(f"Solve Time (sec.): {benders_solver.result.runtime}")
    print(f"Solution: {benders_solver.result.solution}")

.. _manual_decompose_solve:

Automated Decomposition
-------------------------------------------

BendersLib provides an automated decomposition feature through the :class:`AnnotatedBenders` class.
This allows you to decompose a problem by simply providing the original model and specifying the complicating/master variables.
BendersLib will then automatically create the master problem and subproblem.
Here's how to use the automated decomposition feature.

.. code-block:: python

    from benderslib import AnnotatedBenders, ClassicalBenders
    from benderslib.solvers import Gurobi
    from gurobipy import Model, GRB

    # Define the original problem
    def make_original_problem():
        model = Model("Original")
        y = model.addVar(name="y", lb=0, ub=40, vtype=GRB.INTEGER)
        z = model.addVar(name="z", lb=0, ub=40, vtype=GRB.CONTINUOUS)
        model.addConstr(y + z <= 50)
        model.addConstr(2 * y <= 20)
        model.addConstr(2 * y + z >= 10)
        model.setObjective(2 * y + 3 * z, sense=GRB.MINIMIZE)
        model.update()
        complicating_vars = [y.VarName]
        return model, complicating_vars

    # Create an AnnotatedBenders instance
    original_problem, complicating_vars = make_original_problem()
    benders_solver = AnnotatedBenders(
        original_problem=original_problem,
        solver=Gurobi,
        benders=ClassicalBenders,
        complicating_vars=complicating_vars,
    )

    # Solve the problem
    benders_solver.solve()
    print(f"Objective: {benders_solver.result.obj}")
    print(f"Solution: {benders_solver.result.solution}")


In this example, :class:`AnnotatedBenders` takes the complete optimization model,
identifies the master-only and subproblem-only variables and constraints based on the provided ``complicating_vars``,
and then constructs the master problem and subproblem.
Finally, it uses the specified Benders method (:class:`ClassicalBenders` in this case) to solve the decomposed problem.

.. caution::

    You are responsible for **ensuring the type of the master problem and subproblem
    are compatible with the chosen Benders Decomposition method**, based on the given complicating variables
    For example, if your subproblem contains integer variables, and you choose :class:`ClassicalBenders`,
    the algorithm will not function correctly since :class:`ClassicalBenders` assumes a Linear Programming subproblem.

.. admonition:: Example
    :class: seealso

    :ref:`manual_decompose_solve`, :doc:`../examples/basic/annotated_benders`, :doc:`../examples/api/decompose`,
    :doc:`../examples/basic/cbd`

.. _manual_logic_based_benders:

Logic-based Benders Decomposition
-------------------------------------------

BendersLib is highly customizable, allowing you to tailor the decomposition process to your specific needs.
You can :ref:`create custom cut (generators) <manual_custom_cut>`
and :ref:`define your own subproblem logic <manual_custom_sub>`.
A common use case for customization is :doc:`../tutorials/lbbd` where Benders cuts and subproblem solver are problem-specific.
Here is a code snippet showing how to set up a :class:`LogicBasedBenders` instance.

.. code-block:: python

    from benderslib import LogicBasedBenders, MasterProblem, LogicBasedSubProblem, CutGenerator
    from benderslib.solvers import Gurobi

    # Define master problem model
    master_model = ...  # Define your master problem model here
    mp = MasterProblem(Gurobi(master_model))

    # Define a custom logic-based subproblem
    class MyLogicBasedSubProblem(LogicBasedSubProblem):
        def solve():
            # Implement the logic to solve the subproblem given the complicating variable values
            self.status = ...
            self.obj = ...
            self.var_values = ...

    sp = MyLogicBasedSubProblem()

    # Define a custom optimality cut generator
    class MyOptimalityCutGenerator(CutGenerator):
        def generate_cut(self, master_solution, subproblem):
            cuts = []
            # Implement the logic to generate an optimality cut
            cut = ...
            cuts.append(cut)
            return cuts

    # Define complicating variables
    complicating_vars = ['x1', 'x2', 'x3']

    # Initialize and solve
    BD = LogicBasedBenders(mp, sp, complicating_vars, optimality_cut=MyOptimalityCutGenerator)
    BD.solve()

.. _manual_oracle:

BendersLib also allows you to combine subproblem-solving and cut-generation logic in a single component, called **oracle mode**. :class:`Oracle` = subproblem solver + cut generator (optimality and feasibility). :class:`OracleBenders` is an additive LBBD interface.

An oracle is either a function or an :class:`Oracle` subclass. It returns
``(cuts, sub_obj, var_values)``: ``cuts`` is a list of valid :class:`Cut`
instances whose ``ctype`` determines their existing classification;
``sub_obj`` is the recourse objective used to update the upper bound, or
``None`` when no incumbent is available; and ``var_values`` maps subproblem
variable names to their values when ``sub_obj`` is provided.

.. code-block:: python

    from benderslib import Oracle, OracleBenders

    def my_oracle(master_problem):
        master_values = master_problem.get_var_values()
        # Evaluate master_values and create valid Cut instances.
        return cuts, sub_obj, var_values

    benders = OracleBenders(master_problem, my_oracle, complicating_vars)
    benders.solve()

    class MyOracle(Oracle):
        def evaluate(self):
            return my_oracle(self.master_problem)

    benders = OracleBenders(master_problem, MyOracle, complicating_vars)

.. seealso::

    - Abstract base classes for customization:
      :class:`CutGenerator` and :class:`LogicBasedSubProblem`.
    - Class- and function-based customization manul:
      :ref:`Custom Cut (Generator) <manual_custom_cut>` and :ref:`Custom Subproblem(s) <manual_custom_sub>`.
    - The class :class:`LogicBasedBenders` for logic-based Benders decomposition.
    - The classes :class:`Oracle` and :class:`OracleBenders` for oracle-based LBBD.
    - **Executable Examples** (logic-based Benders decomposition):
      :doc:`benders: lbbd <../_tags/benders-lbbd>`
    - **Executable Examples** (oracle mode of logic-based Benders decomposition):
      :doc:`benders: oracle <../_tags/benders-oracle>`
====

Attributes & Methods
-------------------------------------------

The class :class:`BendersSolver` is the base class for all Benders Decomposition implementations.
Specific implementations, e.g., :class:`ClassicalBenders`, inherit from this class.
The diagram below illustrates the main inheritance and composition relationships among the relevant classes.
A :class:`BendersSolver` instance is composed of :class:`MasterProblem`,
:class:`SubProblem` (or :class:`SubProblems`, :class:`LogicBasedSubProblem`),
and :class:`CutGenerator` instances to handle their respective functionalities.

.. mermaid::
    :caption: Benders Solver Inheritance Diagram
    :align: center

    flowchart LR
        BendersSolver -- has --> CutGenerator
        BendersSolver -- has --> MasterProblem
        BendersSolver -- has --> SubProblem

        CutGenerator -- generates --> Cut
        Cut -- is added to --> MasterProblem

        CutGenerator -- uses --> SubProblem
        CutGenerator -- uses --> MasterProblem

        style MasterProblem fill:#f2f2f2,stroke:#333,stroke-width:1px
        style SubProblem fill:#f2f2f2,stroke:#333,stroke-width:1px
        style CutGenerator fill:#f2f2f2,stroke:#333,stroke-width:1px
        style Cut fill:#f2f2f2,stroke:#333,stroke-width:1px

Below are the attributes and methods of the :class:`BendersSolver` class.
Please refer to :doc:`../api/benders` for the attributes and methods of specific implementations.

.. rubric:: :class:`BendersSolver` - Attributes

.. autosummary::
   :nosignatures:

   ~BendersSolver.master_problem
   ~BendersSolver.sub_problem
   ~BendersSolver.complicating_vars
   ~BendersSolver.optimality_cut
   ~BendersSolver.feasibility_cut
   ~BendersSolver.params
   ~BendersSolver.result

.. rubric:: :class:`BendersSolver` - Methods

.. autosummary::
   :nosignatures:

   ~BendersSolver.solve
   ~BendersSolver.from_models

Installation
====================================

.. currentmodule:: benderslib

Installing BendersLib
------------------------------------

.. tip::

   If you are new to Python, we recommend using `conda <https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html>`_
   as your package and environment manager.
   By default, conda will install ``pip`` in the created environments, so you can use either ``pip`` or ``conda``
   to install BendersLib (and other packages).

BendersLib was written in pure Python, you can easily install it via ``pip`` or ``conda``.

Environment Setup (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To avoid potential dependency conflicts, it is recommended to create a new ``conda`` environment
for BendersLib before installing it.

.. code-block:: bash

    # Create a new conda environment named "bendersenv" with Python 3.10 or higher
    conda create -n bendersenv python=3.10

    # Activate the new environment
    conda activate bendersenv

Installing BendersLib
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. caution::

    BendersLib requires Python 3.10 or higher.

.. tab:: pip

    .. code-block:: bash

        python --version
        # Should be Python 3.10 or higher

        pip install benderslib

        # Upgrade to the latest version
        pip install benderslib --upgrade

.. tab:: uv

    .. code-block:: bash

        # Install from PyPI using uv
        uv pip install benderslib

        # Upgrade to the latest version
        uv pip install --upgrade benderslib

Verifying the Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To verify that BendersLib has been installed correctly, you can run the following code:

.. code-block:: python

    import benderslib as bd

    print("BendersLib version:", bd.__version__)

If you see the version number printed without any errors, the installation was successful.

.. _manual_installing_solver:

Installing Solvers
------------------------------------

.. attention::

   BendersLib will **NOT** install any solver to your environment automatically.
   You need to install the solvers separately based on your needs.

BendersLib supports several popular optimization solvers.
You can install these solvers individually based on your needs. Installing all of them is not necessary.
Please refer to :ref:`solver-table` for solver features and license requirements

.. code-block:: bash

    # Install only needed solvers
    pip install "benderslib[copt]"
    pip install "benderslib[cplex]"
    pip install "benderslib[cplexcp]"
    pip install "benderslib[gurobi]"
    pip install "benderslib[ortools]"
    pip install "benderslib[pyomo]"
    pip install "benderslib[scip]"

    # Install all supported solvers
    pip install "benderslib[all-solvers]"

You can also install solvers via ``conda``. Please refer to the table below for the specific commands.

.. list-table:: Installing Solvers
    :widths: auto
    :header-rows: 1
    :name: solver-installation-table

    * - Solver
      - pip
      - conda
      - Guide
    * - **COPT**
      - ``pip install coptpy``
      - N/A
      - `Install <https://guide.coap.online/copt/en-doc/pythoninterface.html#chappythoninterface>`__
    * - **CPLEX**
      - ``pip install cplex``
      - ``conda install ibmdecisionoptimization::cplex``
      - `Install <https://www.ibm.com/docs/en/icos/22.1.2?topic=cplex-installing>`__ [1]_
    * - **CP Optimizer**
      - ``pip install docplex``
      - ``conda install ibmdecisionoptimization::docplex``
      - `Install <https://www.ibm.com/docs/en/icos/22.1.2?topic=cplex-installing>`__ [1]_
    * - **Gurobi**
      - ``pip install gurobipy``
      - ``conda install gurobi::gurobi``
      - `Install <https://support.gurobi.com/hc/en-us/articles/360044290292-How-do-I-install-Gurobi-for-Python>`__
    * - **OR-Tools**
      - ``pip install ortools``
      - N/A
      - `Install <https://developers.google.com/optimization/install/python>`__
    * - **SCIP**
      - ``pip install pyscipopt``
      - ``conda install conda-forge::pyscipopt``
      - `Install <https://pyscipopt.readthedocs.io/en/latest/install.html>`__
    * - **Pyomo** [2]_:
      - ``pip install pyomo``
      - ``conda install conda-forge::pyomo``
      - `Install <https://pyomo.readthedocs.io/en/stable/getting_started/installation.html>`__
    * - CBC
      - N/A
      - ``conda install conda-forge::coincbc``
      - `Install <https://github.com/coin-or/Cbc>`__
    * - CPLEX
      - ``pip install cplex``
      - ``conda install ibmdecisionoptimization::cplex``
      - `Install <https://www.ibm.com/docs/en/icos/22.1.2?topic=cplex-installing>`__
    * - GLPK
      - N/A
      - ``conda install conda-forge::glpk``
      - `Install <https://www.gnu.org/software/glpk/#downloading>`__
    * - Gurobi
      - ``pip install gurobipy``
      - ``conda install gurobi::gurobi``
      - `Install <https://support.gurobi.com/hc/en-us/articles/360044290292-How-do-I-install-Gurobi-for-Python>`__
    * - HiGHS
      - ``pip install highspy``
      - ``conda install conda-forge::highspy``
      - `Install <https://ergo-code.github.io/HiGHS/dev/interfaces/python/>`__
    * - MOSEK
      - ``pip install mosek``
      - ``conda install mosek::MOSEK``
      - `Install <https://docs.mosek.com/latest/install/installation.html>`__
    * - SCIP
      - N/A
      - ``conda install conda-forge::scip``
      - `Install <https://www.scipopt.org>`__
    * - Xpress
      - ``pip install xpress``
      - ``conda install fico-xpress::xpress``
      - `Install <https://www.fico.com/fico-xpress-optimization/docs/latest/installguide/dhtml/chapinst1.html>`__

.. [1] *Previous commands install only the Python API. You still need to install the solver engine separately.*
.. [2]  *Pyomo is a modeling language. Supported solvers must be installed separately, see*
        `installation instruction <https://pyomo.readthedocs.io/en/stable/getting_started/solvers.html>`_ *and*
        `supported solvers <https://github.com/Pyomo/pyomo/tree/main/pyomo/solvers/plugins/solvers>`_ *(by Pyomo)*.

Troubleshooting
------------------------------------

*To be added (common issues will be summarized here)...*

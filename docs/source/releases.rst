Release Notes
===================================

.. note::

    This project uses `Semantic Versioning <https://semver.org/>`_ for version numbering:

    - The version number is in the format of ``MAJOR.MINOR.PATCH``. An increment in the ``MAJOR``
      version indicates incompatible API changes, an increment in the ``MINOR`` version indicates
      added functionality in a backward-compatible manner, and an increment in the ``PATCH`` version
      indicates backward-compatible bug fixes.
    - **Major version zero (0.y.z) is for beta releases. Anything may change at any time.
      The public API should not be considered stable till version 1.y.z.**

v0.6.1 (Beta) - Forthcoming
------------------------------------

**Added**

-   [ci] Add release wheel tests before publishing to PyPI
    (`#38 <https://github.com/phguo/BendersLib/pull/38>`_).
-   [docs] Add a how-to guide for converting models between solvers
    (`#44 <https://github.com/phguo/BendersLib/pull/44>`_).

**Fixed**

-   Fix handling of unbounded master relaxations by raising an error
    (`#39 <https://github.com/phguo/BendersLib/pull/39>`_).
-   Fix scenario weight count validation and estimator weights in Pyomo
    (`#40 <https://github.com/phguo/BendersLib/pull/40>`_).
-   Fix estimator name conflicts with master problem variables
    (`#41 <https://github.com/phguo/BendersLib/pull/41>`_).
-   Fix objective constant handling in annotated decomposition
    (`#42 <https://github.com/phguo/BendersLib/pull/42>`_).
-   Fix binary cut validation to reject non-binary variable values
    (`#43 <https://github.com/phguo/BendersLib/pull/43>`_).
-   Fix objective sense validation in automatic decomposition
    (`#45 <https://github.com/phguo/BendersLib/pull/45>`_).
-   Fix JSON result export by converting non-finite values to null
    (`#46 <https://github.com/phguo/BendersLib/pull/46>`_).
-   Fix propagation of parameters and complicating variables to scenario subproblems
    (`#47 <https://github.com/phguo/BendersLib/pull/47>`_).

v0.6.0 (Beta) - 2026-11-08
------------------------------------

This release introduces Oracle Mode, which combines custom subproblem solving
and cut generation in a single interface.

**Added**

-   Add Oracle Mode for combined custom subproblem solving and cut generation
    (`#24 <https://github.com/phguo/BendersLib/pull/24>`_,
    `#27 <https://github.com/phguo/BendersLib/pull/27>`_).
-   Add COPT benchmarks
    (`#15 <https://github.com/phguo/BendersLib/pull/15>`_).
-   [test] Add solution consistency tests
    (`#30 <https://github.com/phguo/BendersLib/pull/30>`_).
-   [ci] Add a GitHub Actions check for documentation builds
    (`#28 <https://github.com/phguo/BendersLib/pull/28>`_).
-   [ci] Add TestPyPI publishing
    (`#37 <https://github.com/phguo/BendersLib/pull/37>`_).

**Changed**

-   Remove the PyYAML dependency
    (`#9 <https://github.com/phguo/BendersLib/pull/9>`_).
-   Require Sphinx 9.0.0 or later
    (`#17 <https://github.com/phguo/BendersLib/pull/17>`_).
-   Extend COPT support to Python 3.14
    (`#19 <https://github.com/phguo/BendersLib/pull/19>`_).
-   [ci] Run tests on macOS 15 to stabilize COPT testing
    (`#25 <https://github.com/phguo/BendersLib/pull/25>`_,
    `#34 <https://github.com/phguo/BendersLib/pull/34>`_).
-   [test] Exclude raise statements from coverage reports
    (`#36 <https://github.com/phguo/BendersLib/pull/36>`_).
-   [docs] Improve documentation
    (`#11 <https://github.com/phguo/BendersLib/pull/11>`_,
    `#16 <https://github.com/phguo/BendersLib/pull/16>`_,
    `#20 <https://github.com/phguo/BendersLib/pull/20>`_,
    `#21 <https://github.com/phguo/BendersLib/pull/21>`_,
    `#22 <https://github.com/phguo/BendersLib/pull/22>`_,
    `#23 <https://github.com/phguo/BendersLib/pull/23>`_,
    `#26 <https://github.com/phguo/BendersLib/pull/26>`_,
    `#29 <https://github.com/phguo/BendersLib/pull/29>`_).

**Fixed**

-   Fix Pyomo constraint offsets, estimator bounds, cut removal, and active objective detection
    (`#34 <https://github.com/phguo/BendersLib/pull/34>`_).
-   Fix SCIP interface bugs in branch-and-check, IIS extraction, and equality constraint handling
    (`#30 <https://github.com/phguo/BendersLib/pull/30>`_).
-   Fix integer rounding when fixing values in CP subproblems
    (`#33 <https://github.com/phguo/BendersLib/pull/33>`_).
-   Fix COPT reoptimization after an infeasible solve when variable bounds change
    (`#30 <https://github.com/phguo/BendersLib/pull/30>`_).
-   Fix missing final solve status in JSON results and reject repeated solves on the same solver instance
    (`#35 <https://github.com/phguo/BendersLib/pull/35>`_).

v0.5.1 (Beta) - 2026-04-29
-------------------------------------

**Added**

-   Add a GitHub Actions workflow for automatic releases on PyPI.
-   Add a ``CITATION.cff`` file for citation metadata.
-   [docs] Add ``.readthedocs.yaml`` for Read the Docs integration.
-   [docs] Add sitemap using ``sphinx_sitemap``.

**Changed**

-   Make ``matplotlib`` an optional dependency.
-   Update the dependencies for benchmarking.
-   [docs] Update the logos in the documentation.

**Fixed**

-   Fix a bug caused by inconsistent placeholder solver names.

v0.5.0 (Beta) - 2026-04-17
-------------------------------------

We are excited to announce the first public beta release of *BendersLib*,
a Python library dedicated to Benders decomposition!
To get started, please see the :doc:`Quickstart <index>` section in our documentation.
We welcome any feedback. Please report any issues
or suggestions on our `GitHub Issues page <https://github.com/phguo/BendersLib/issues>`_.
We also welcome contributions to the library.

**Added**

-   **Benders Decomposition Variants**:
    :doc:`Classical Benders Decomposition <tutorials/classical>`,
    :doc:`Combinatorial Benders Decomposition <tutorials/cbd>`,
    :doc:`Generalized Benders Decomposition <tutorials/gbd>`,
    :doc:`L-shaped Method <tutorials/lshaped>` (linear and convex recourse),
    :doc:`Integer L-shaped Method <tutorials/ilshaped>`, and
    :doc:`Logic-based Benders Decomposition <tutorials/lbbd>`.

-   **Extensibility**:
    :ref:`Annotated Benders Decomposition <manual_decompose_solve>`,
    :ref:`Custom Cut Generation <manual_custom_cut>`,
    :ref:`Custom Subproblem Solvers <manual_custom_sub>`, and
    :doc:`Callbacks </manual/callbacks>`.

-   **Enhancement Options**:
    :ref:`Branch-and-check Method <enhance_branch_and_check>`,
    :ref:`Parallel Subproblem Solving <enhance_parallel>`,
    :ref:`Multi-cut Generation <enhance_multi_cut>`,
    :ref:`Cut Normalization <enhance_cut_normalization>`, and
    IIS-based Feasibility Cut Generation (:attr:`~benderslib.BendersParams.use_iis_cut`).

-   **Solver Agnostic**:
    Built-in interfaces for :ref:`popular solvers <solver-table>`.

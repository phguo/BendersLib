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

Version 0.6.0 (Beta) - Forthcoming
------------------------------------

.. rubric:: Changed

*   Remove ``PyYAML>=6.0.0`` dependency by replacing ``config.yaml`` with ``config.py`` (`#9 <https://github.com/phguo/BendersLib/pull/9>`_).

Version 0.5.1 (Beta) - 2026-04-29
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

Version 0.5.0 (Beta) - 2026-04-17
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

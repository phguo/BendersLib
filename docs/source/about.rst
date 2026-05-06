About
================================

**BendersLib** (https://benders.dev) is a Python library that supports a range of Benders decomposition variants,
including :doc:`tutorials/classical`, :doc:`tutorials/cbd`, :doc:`tutorials/lshaped`, :doc:`tutorials/ilshaped`,
:doc:`tutorials/gbd`, and :doc:`tutorials/lbbd`.
While BendersLib provides :doc:`built-in implementations of these methods <api/benders>`,
it is designed to be extensible. Users can implement custom Benders decomposition methods by
customizing :ref:`subproblem solvers <manual_custom_sub>` and :ref:`cut generators <manual_custom_cut>`,
and defining :doc:`callback functions <manual/callbacks>` for :doc:`enhancement strategies <tutorials/enhance>`.
BendersLib is solver agnostic and has :doc:`built-in interfaces <manual/solvers>` for
popular Mathematical Programming and Constraint Programming solvers.
Its support for rapid prototyping and high extensibility are designed to meet the needs of
both researchers and practitioners in Operations Research and related fields.

.. list-table:: BendersLib Resources
   :widths: 25 75

   * - **Documentation**
     - `https://benders.dev <https://benders.dev>`_
   * - **GitHub Repository**
     - `https://github.com/phguo/BendersLib <https://github.com/phguo/BendersLib>`_
   * - **PyPI Package**
     - `https://pypi.org/project/BendersLib <https://pypi.org/project/BendersLib>`_
   * - **Paper**
     -

------

Contributors
--------------------------------

BendersLib was created by **Peng-Hui Guo** ("郭鹏辉" in Chinese, https://guo.ph),
who holds a PhD in Management Science and Engineering
from Nanjing University of Aeronautics and Astronautics (NUAA), China.

*Contributions to BendersLib are welcome! If you would like to contribute, please visit*
:doc:`manual/contribution` *for more information.*

.. contributors:: phguo/BendersLib
    :avatars:
    :limit: 100
    :exclude: copilot-swe-agent, Copilot

------

Citing BendersLib
--------------------------------

    Guo, P. (2026). BendersLib: A Benders Decomposition Library in Python (Version 0.5.1) [Computer software]. https://github.com/phguo/BendersLib

.. code-block:: bibtex

    @software{GuoBendersLib2026,
        author = {Guo, Penghui},
        license = {Apache-2.0},
        month = apr,
        title = {{BendersLib: A Benders Decomposition Library in Python}},
        url = {https://github.com/phguo/BendersLib},
        version = {0.5.1},
        year = {2026}
    }

.. rubric:: Papers Citing BendersLib

*We update this list regularly. If you have a paper citing
BendersLib and would like it listed here, please let us know!*

------

License
-----------------------------------

BendersLib is licensed under the `Apache-2.0 License <https://github.com/phguo/BendersLib?tab=Apache-2.0-1-ov-file>`__.

------

Logo
--------------------------------

.. rubric:: Logo (horizontal)

.. image:: _static/benderslib.png
   :align: left

.. rubric:: Logo (vertical)

.. image:: _static/benderslib_v.png
   :align: left
   :height: 350px
   :width: 350px

# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from ..consts import BendersConsts as CST
from ..core import CutGenerator
from .cuts import (
    ClassicalOC,
    ClassicalFC,
    NoGoodFC,
    CombinatorialOC,
    LShapedOC,
    GeneralizedOC,
    GeneralizedFC,
    GeneLShapedOC,
)


class ClassicalOCGen(CutGenerator):
    """The optimality cut generator for :doc:`../tutorials/classical`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

        self.var_coefs = sub_problem.get_var_coefs(self.complicating_vars)
        self.rhs = sub_problem.get_rhs()

    def generate(self) -> list[ClassicalOC]:
        """
        This method generates :class:`ClassicalOC` optimality cuts based on the current solution
        of the master problem and the dual values obtained from the subproblem.
        """
        dual_values = self.sub_problem.get_dual_values()

        cut = ClassicalOC(self.complicating_vars, self.var_coefs, dual_values, self.rhs)
        return [cut]


class ClassicalFCGen(CutGenerator):
    """The feasibility cut generator for :doc:`../tutorials/classical`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

        self.var_coefs = sub_problem.get_var_coefs(self.complicating_vars)
        self.rhs = sub_problem.get_rhs()

    def generate(self) -> list[ClassicalFC]:
        """
        This method generates :class:`ClassicalFC` feasibility cuts based on the current solution
        of the master problem and the extreme ray obtained from the subproblem.
        """
        extreme_ray = self.sub_problem.get_extreme_ray()

        cut = ClassicalFC(self.complicating_vars, self.var_coefs, extreme_ray, self.rhs)
        return [cut]


class CombinatorialFCGen(CutGenerator):
    """The feasibility cut generator for :doc:`../tutorials/cbd`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

    def generate(self) -> list[NoGoodFC]:
        """
        This method generates :class:`NoGoodFC` feasibility cuts based on the current solution
        of the master problem.
        """
        var_names = self.complicating_vars
        if self.params.use_iis_cut:
            var_names = self.sub_problem.compute_iis()

        var_names = list(set(var_names) & set(self.complicating_vars))
        var_values = self.master_problem.get_var_values(var_names)

        cut = NoGoodFC(var_values, tol_binary=self.params.tol_binary)
        return [cut]


class CombinatorialOCGen(CutGenerator):
    """The optimality cut generator for :doc:`../tutorials/cbd`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

    def generate(self) -> list[CombinatorialOC]:
        """
        This method generates :class:`CombinatorialOC` optimality cuts based on the current solution
        of the master problem and the objective value obtained from the subproblem.
        """
        var_values = self.master_problem.get_var_values(self.complicating_vars)
        sub_obj = self.sub_problem.get_obj()
        estimator = self.master_problem.estimators[0]
        theta_lb = self.master_problem.get_estimator_values()[estimator]

        cut = CombinatorialOC(
            var_values, sub_obj,
            big_m=sub_obj - theta_lb, estimator=estimator,
            tol_binary=self.params.tol_binary
        )
        return [cut]


class LShapedOCGen(CutGenerator):
    """The optimality cut generator for :doc:`../tutorials/lshaped` (linear recourse)."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

        self.var_coefs = dict()
        self.rhs = dict()

        for i, sub in enumerate(self.sub_problem):
            self.var_coefs[i] = sub.get_var_coefs(self.complicating_vars)
            self.rhs[i] = sub.get_rhs()

    def _single_cut(self) -> list[LShapedOC]:
        """
        This method generates a single :class:`LShapedOC` optimality cut aggregating all subproblems (scenarios).
        """
        complicating_vars = self.complicating_vars

        all_probs = [self.sub_problem.prob[i] for i in range(len(self.sub_problem))]
        all_duals = [sub.get_dual_values() for sub in self.sub_problem]
        all_rhss = [self.rhs[i] for i in range(len(self.sub_problem))]
        all_var_coefs = [self.var_coefs[i] for i in range(len(self.sub_problem))]

        cut = LShapedOC(complicating_vars, all_probs, all_duals, all_rhss, all_var_coefs)
        return [cut]

    def _multi_cuts(self) -> list[ClassicalOC]:
        """
        This method generates multiple :class:`ClassicalOC` optimality cuts, one for each subproblem (scenario).
        """
        cuts = []
        for i, sub in enumerate(self.sub_problem):
            _var_coefs = self.var_coefs[i]
            _rhs = self.rhs[i]
            _dual = sub.get_dual_values()

            vars = self.complicating_vars
            estimator = self.master_problem.estimators[i]

            # Add the cut only if it is violated
            if sub.get_obj() - self.master_problem.get_estimator_values()[estimator] > self.params.tol_obj_diff:
                cut = ClassicalOC(vars, _var_coefs, _dual, _rhs, estimator=estimator)
                cuts.append(cut)

        return cuts

    def generate(self) -> list[ClassicalOC] | list[LShapedOC]:
        """
        This method generates optimality cuts based on the current solution
        of the master problem and the dual values obtained from the subproblems.
        If :attr:`BendersParams.multi_opti_cut` is ``True``, :func:`_multi_cuts` is called to generate multiple cuts;
        otherwise, :func:`_single_cut` is called to generate a single aggregated cut.
        """
        return self._multi_cuts() if self.params.multi_opti_cut else self._single_cut()


class LShapedFCGen(CutGenerator):
    """The feasibility cut generator for :doc:`../tutorials/lshaped`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

        self.var_coefs = dict()
        self.rhs = dict()

        for i, sub in enumerate(self.sub_problem):
            self.var_coefs[i] = sub.get_var_coefs(self.complicating_vars)
            self.rhs[i] = sub.get_rhs()

    def generate(self) -> list[ClassicalFC]:
        """
        This method generates :class:`ClassicalFC` feasibility cuts based on the current solution
        of the master problem and the extreme rays obtained from the subproblems.
        """
        cuts = []

        for i, sub in enumerate(self.sub_problem):
            if sub.status == CST.INFEASIBLE:
                _var_coefs = self.var_coefs[i]
                _rhs = self.rhs[i]
                _extreme_ray = sub.get_extreme_ray()

                cut = ClassicalFC(self.complicating_vars, _var_coefs, _extreme_ray, _rhs)
                cuts.append(cut)
                if not self.params.multi_feas_cut:
                    break

        return cuts


class IntegerLShapedOCGen(CutGenerator):
    """The optimality cut generator for :doc:`../tutorials/ilshaped`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

    def _single_cut(self) -> list[CombinatorialOC]:
        """
        This method generates a single :class:`CombinatorialOC` optimality cut aggregating all subproblems (scenarios).
        """
        bin_var_values = self.master_problem.get_var_values(self.complicating_vars)
        sub_obj = self.sub_problem.get_obj()
        estimator = self.master_problem.estimators[0]
        theta_lb = self.master_problem.get_estimator_values()[estimator]

        cuts = []
        if sub_obj - theta_lb > self.params.tol_obj_diff:
            cut = CombinatorialOC(
                bin_var_values, sub_obj,
                big_m=sub_obj - theta_lb, estimator=estimator,
                tol_binary=self.params.tol_binary
            )
            cuts.append(cut)

        return cuts

    def _multi_cuts(self) -> list[CombinatorialOC]:
        """
        This method generates multiple :class:`CombinatorialOC` optimality cuts, one for each subproblem (scenario).
        """
        cuts = []

        for i, sub in enumerate(self.sub_problem):
            bin_var_values = self.master_problem.get_var_values(self.complicating_vars)
            sub_obj = sub.get_obj()
            estimator = self.master_problem.estimators[i]
            theta = self.master_problem.get_estimator_values()[estimator]

            # Add the cut only if it is violated
            if sub_obj - theta > self.params.tol_obj_diff:
                cut = CombinatorialOC(
                    bin_var_values, sub_obj,
                    big_m=sub_obj - theta, estimator=estimator,
                    tol_binary=self.params.tol_binary
                )
                cuts.append(cut)

        return cuts

    def generate(self):
        """
        This method generates optimality cuts based on the current values of binary complicating variables
        in the master problem and the objective values obtained from the subproblems.
        If :attr:`BendersParams.multi_opti_cut` is ``True``, :func:`_multi_cuts` is called to generate multiple cuts;
        otherwise, :func:`_single_cut` is called to generate a single aggregated cut.
        """
        return self._multi_cuts() if self.params.multi_opti_cut else self._single_cut()


class IntegerLShapedFCGen(CutGenerator):
    """The feasibility cut generator for :doc:`../tutorials/ilshaped`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

    def generate(self) -> list[NoGoodFC]:
        """
        This method generates :class:`NoGoodFC` feasibility cuts based on the current values of binary
        complicating variables in the master problem.
        """
        bin_var_values = self.master_problem.get_var_values(self.complicating_vars)
        cut = NoGoodFC(bin_var_values, tol_binary=self.params.tol_binary)

        return [cut]


class GeneralizedOCGen(CutGenerator):
    """The optimality cut generator for :doc:`../tutorials/gbd`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

        self.var_coefs = sub_problem.get_var_coefs(self.complicating_vars)

    def generate(self) -> list[GeneralizedOC]:
        """This method generates :class:`GeneralizedOC` optimality cuts."""
        sub_obj = self.sub_problem.get_obj()
        lagrange_multipliers = self.sub_problem.get_dual_values()
        master_vars_values = self.master_problem.get_var_values(self.complicating_vars)

        cut = GeneralizedOC(
            self.complicating_vars,
            master_vars_values,
            self.var_coefs,
            sub_obj,
            lagrange_multipliers,
        )
        return [cut]


class GeneralizedFCGen(CutGenerator):
    """The feasibility cut generator for :doc:`../tutorials/gbd`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

        self.var_coefs = sub_problem.get_var_coefs(self.complicating_vars)
        self.rhs = sub_problem.get_rhs()

    def generate(self) -> list[ClassicalFC]:
        """This method generates :class:`GeneralizedFC` feasibility cuts."""
        extreme_ray = self.sub_problem.get_extreme_ray()

        cut = GeneralizedFC(self.complicating_vars, self.var_coefs, extreme_ray, self.rhs)
        return [cut]


class GeneLShapedOCGen(CutGenerator):
    """The optimality cut generator for :doc:`../tutorials/lshaped` (convex recourse)."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

        self.var_coefs = dict()
        for i, sub in enumerate(self.sub_problem):
            self.var_coefs[i] = sub.get_var_coefs(self.complicating_vars)

    def _single_cut(self) -> list[GeneLShapedOC]:
        """Generates a single aggregated :class:`GeneLShapedOC` from all scenarios."""
        complicating_vars = self.complicating_vars
        var_values = self.master_problem.get_var_values(complicating_vars)

        all_probs = []
        all_sub_objs = []
        all_multipliers = []
        all_var_coefs = []

        for i, sub in enumerate(self.sub_problem):
            all_probs.append(self.sub_problem.prob[i])
            all_sub_objs.append(sub.get_obj())
            all_multipliers.append(sub.get_dual_values())
            all_var_coefs.append(self.var_coefs[i])

        cut = GeneLShapedOC(
            complicating_vars,
            all_probs,
            var_values,
            all_var_coefs,
            all_sub_objs,
            all_multipliers,
        )
        return [cut]

    def _multi_cuts(self) -> list[GeneralizedOC]:
        """Generates multiple :class:`GeneralizedOC` cuts, one for each subproblem (scenario)."""
        cuts = []
        var_values = self.master_problem.get_var_values(self.complicating_vars)

        for i, sub in enumerate(self.sub_problem):
            estimator = self.master_problem.estimators[i]
            theta = self.master_problem.get_estimator_values()[estimator]
            sub_obj = sub.get_obj()

            # Add the cut only if it is violated
            if sub_obj - theta > self.params.tol_obj_diff:
                cut = GeneralizedOC(
                    vars=self.complicating_vars,
                    var_values=var_values,
                    var_coefs=self.var_coefs[i],
                    sub_obj=sub_obj,
                    multipliers=sub.get_dual_values(),
                    estimator=estimator
                )
                cuts.append(cut)

        return cuts

    def generate(self) -> list[GeneLShapedOC] | list[GeneralizedOC]:
        """Generates optimality cuts for the generalized L-shaped method.

        If :attr:`BendersParams.multi_opti_cut` is ``True``, this method calls :func:`_multi_cuts`
        to generate multiple :class:`GeneralizedOC`, one for each violated scenario;
        If ``False``, it calls :func:`_single_cut` to generate one aggregated
        :class:`GeneLShapedOC` for all scenarios.
        """
        return self._multi_cuts() if self.params.multi_opti_cut else self._single_cut()

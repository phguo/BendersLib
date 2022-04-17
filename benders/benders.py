# coding:utf-8

from gurobipy import Model, LinExpr


class Benders(object):

    def __init__(self, original_model):
        original_model.update()
        self.master_keyword = "__M__"

        self.original_model = original_model
        self.master_model = self._get_master_model(original_model)
        self.sub_model = self._get_sub_model(original_model)

    def _get_master_model(self, model):
        # Fetch original vars
        model_vars_dict = {
            var.VarName: var for var in model.getVars() if self.master_keyword in var.VarName}

        # Fetch original constraints
        model_constrs_dict = {
            constr.ConstrName: constr for constr in model.getConstrs()
            if self.master_keyword in constr.ConstrName}

        # Copy variables to master model
        new_model = Model()
        for v in model_vars_dict.values():
            new_model.addVar(lb=v.lb, ub=v.ub, obj=v.obj, vtype=v.vtype, name=v.VarName, column=None)
        new_model.update()
        new_model_vars_dict = {var.VarName: var for var in new_model.getVars()}

        # Copy constraints to master model
        for c in model_constrs_dict.values():
            expr = model.getRow(c)
            var_list = [new_model_vars_dict[expr.getVar(i).VarName] for i in range(expr.size())]
            coefficient_list = [expr.getCoeff(i) for i in range(expr.size())]
            new_expr = LinExpr(coefficient_list, var_list)
            new_model.addLConstr(new_expr, c.Sense, c.RHS, name=c.ConstrName)

        new_model.update()
        return new_model

    def _get_sub_model(self, model, master_var_vals=None):
        # Fetch original vars
        model_vars_dict = {var.VarName: var for var in model.getVars()}

        # Fetch original constraints
        model_constrs_dict = {
            constr.ConstrName: constr for constr in model.getConstrs()
            if not self.master_keyword in constr.ConstrName}

        # Copy variables to master model
        new_model = Model()
        for v in model_vars_dict.values():
            new_model.addVar(lb=v.lb, ub=v.ub, obj=v.obj, vtype=v.vtype, name=v.VarName, column=None)
        new_model.update()
        new_model_vars_dict = {var.VarName: var for var in new_model.getVars()}

        # Copy constraints to master model
        for c in model_constrs_dict.values():
            expr = model.getRow(c)
            var_list = [new_model_vars_dict[expr.getVar(i).VarName] for i in range(expr.size())]
            coefficient_list = [expr.getCoeff(i) for i in range(expr.size())]
            new_expr = LinExpr(coefficient_list, var_list)
            new_model.addLConstr(new_expr, c.Sense, c.RHS, name=c.ConstrName)

        if master_var_vals:
            for var_name, var_value in master_var_vals.items():
                if new_model.getVarByName(var_name):
                    new_model.getVarByName(var_name).lb = var_value
                    new_model.getVarByName(var_name).ub = var_value

        new_model.update()
        return new_model


class ClassicalBenders(Benders):
    def __init__(self, original_model, master_model, sub_model, link_variables):
        Benders.__init__(self, original_model)


class CombinatorialBenders(Benders):
    def __init__(self, original_model, master_model, sub_model, link_variables):
        Benders.__init__(self, original_model)


class GeneralizedBenders(Benders):
    def __init__(self, original_model, master_model, sub_model, link_variables):
        Benders.__init__(self, original_model)


class LogicbasedBenders(Benders):
    def __init__(self, original_model, master_model, sub_model, link_variables, feasibility_cuts, optimality_cuts):
        Benders.__init__(self, original_model)


def main():
    pass


if __name__ == '__main__':
    main()

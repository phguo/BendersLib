# coding:utf-8

from gurobipy import Model, GRB
from benders.benders import Benders

if __name__ == '__main__':
    model = Model()

    # Add some variables
    var_index = [i for i in range(10)]
    master_vars = model.addVars(var_index, vtype=GRB.CONTINUOUS, name="__M__master_vars")
    sub_vars = model.addVars(var_index, vtype=GRB.CONTINUOUS, name="master_vars")

    # Add some linear constraints
    model.addConstr(master_vars.sum("*") == 1, name="__M__master_constrs")
    model.addConstrs((master_vars[i] + sub_vars[i] <= 1 for i in var_index), name="sub_constrs")

    benders = Benders(model)
    master_model = benders.master_model
    sub_model = benders.sub_model

    master_model.optimize()
    sub_model.optimize()

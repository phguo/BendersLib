# BendersLib: a Benders decomposition library
```
 ____                       __                        __           __        
/\  _`\                    /\ \                      /\ \       __/\ \       
\ \ \L\ \     __    ___    \_\ \     __   _ __   ____\ \ \     /\_\ \ \____  
 \ \  _ <'  /'__`\/' _ `\  /'_` \  /'__`\/\`'__\/',__\\ \ \  __\/\ \ \ '__`\ 
  \ \ \L\ \/\  __//\ \/\ \/\ \L\ \/\  __/\ \ \//\__, `\\ \ \L\ \\ \ \ \ \L\ \
   \ \____/\ \____\ \_\ \_\ \___,_\ \____\\ \_\\/\____/ \ \____/ \ \_\ \_,__/
    \/___/  \/____/\/_/\/_/\/__,_ /\/____/ \/_/ \/___/   \/___/   \/_/\/___/ 
```

BendersLib is a Benders decomposition library written in Python.

Supported Benders decomposition variants:

- Classical Benders decomposition
- Combinatorial Benders decomposition
- Generalized Benders decomposition
- Logic-based Benders decomposition

---

## 1. Classical Benders decomposition

Classical Benders decomposition (BD) solves mixed-integer linear programming (MILP) with linear mixed-integer master problem and linear continues sub problem.

## 2. Combinatorial Benders decomposition

Combinatorial Benders decomposition (CBD) can handle 0-1 integer master problem and feasibility checking subproblem (a programming with objective function be set to 0).

## 3. Generalized Benders decomposition

Generalized Benders decomposition (GBD) solves nonlinear programming for which the subproblem is a convex program.

## 4. Logic-based Benders decomposition

Logic-based Benders decomposition (LBBD) can be used for problems which can be decomposed into any type of master and sub problem.

---

## Reference

1. Benders, J.F., 1962. Partitioning procedures for solving mixed-variables programming problems. Numer. Math. 4, 238–252. https://doi.org/10.1007/BF01386316
2. Codato, G., Fischetti, M., 2006. Combinatorial Benders’ Cuts for Mixed-Integer Linear Programming. Operations Research 54, 756–766. https://doi.org/10.1287/opre.1060.0286
3. Geoffrion, A.M., 1972. Generalized Benders decomposition. J Optim Theory Appl 10, 237–260. https://doi.org/10.1007/BF00934810
4. Hooker, J.N., Ottosson, G., 2003. Logic-based Benders decomposition. Math. Program., Ser. A 96, 33–60. https://doi.org/10.1007/s10107-003-0375-9
5. Rahmaniani, R., Crainic, T.G., Gendreau, M., Rei, W., 2017. The Benders decomposition algorithm: A literature review. European Journal of Operational Research 259, 801–817. https://doi.org/10.1016/j.ejor.2016.12.005


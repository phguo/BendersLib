Minimize
 cost: 3 capacity + production1 + 3 production2 + inventory1
Subject To
 balance1: production1 - inventory1 = 3
 balance2: inventory1 + production2 = 5
 capacity1: production1 - 4 capacity <= 0
 capacity2: production2 - 4 capacity <= 0
Bounds
 0 <= capacity <= 3
 production1 >= 0
 production2 >= 0
 inventory1 >= 0
General
 capacity
End

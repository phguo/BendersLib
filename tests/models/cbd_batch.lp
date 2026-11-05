Minimize
 cost: 3 enable1 + 5 enable2 + 2 batch1 + 3 batch2
Subject To
 demand: 2 batch1 + 3 batch2 >= 5
 capacity1: batch1 - 3 enable1 <= 0
 capacity2: batch2 - 2 enable2 <= 0
Bounds
 batch1 >= 0
 batch2 >= 0
General
 batch1 batch2
Binary
 enable1 enable2
End

Minimize
 cost: 5 open1 + 7 open2 + ship11 + 4 ship12 + 3 ship21 + ship22
Subject To
 capacity1: ship11 + ship12 - 6 open1 <= 0
 capacity2: ship21 + ship22 - 8 open2 <= 0
 demand1: ship11 + ship21 = 4
 demand2: ship12 + ship22 = 5
Bounds
 ship11 >= 0
 ship12 >= 0
 ship21 >= 0
 ship22 >= 0
Binary
 open1 open2
End

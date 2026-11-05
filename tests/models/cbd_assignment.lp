Minimize
 cost: 3 open1 + 4 open2 + assign11 + 2 assign12 + 4 assign13 + 4 assign21 + assign22 + 2 assign23
Subject To
 customer1: assign11 + assign21 = 1
 customer2: assign12 + assign22 = 1
 customer3: assign13 + assign23 = 1
 capacity1: 2 assign11 + 2 assign12 + 3 assign13 - 4 open1 <= 0
 capacity2: 2 assign21 + 2 assign22 + 3 assign23 - 4 open2 <= 0
Binary
 open1 open2 assign11 assign12 assign13 assign21 assign22 assign23
End

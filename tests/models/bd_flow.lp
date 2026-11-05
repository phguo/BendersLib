Minimize
 cost: 2 open_sa + 2 open_at + open_sb + open_bt + flow_sa + flow_at + 2 flow_sb + 2 flow_bt
Subject To
 source: flow_sa + flow_sb = 3
 node_a: flow_sa - flow_at = 0
 node_b: flow_sb - flow_bt = 0
 sink: flow_at + flow_bt = 3
 capacity_sa: flow_sa - 4 open_sa <= 0
 capacity_at: flow_at - 4 open_at <= 0
 capacity_sb: flow_sb - 5 open_sb <= 0
 capacity_bt: flow_bt - 5 open_bt <= 0
Bounds
 flow_sa >= 0
 flow_at >= 0
 flow_sb >= 0
 flow_bt >= 0
Binary
 open_sa open_at open_sb open_bt
End

\ Sample QUBO instance
Minimize
  -17 x0 + 10 x0 x1 + 10 x0 x2 + 10 x0 x3 + 20 x0 x5
  -18 x1 + 10 x1 x2 + 10 x1 x3 + 10 x1 x4 + 20 x1 x5
  -29 x2 + 10 x2 x3 + 20 x2 x4 + 20 x2 x5
  -19 x3 + 10 x3 x4 + 10 x3 x5
  -17 x4 + 10 x4 x5
  -28 x5
Subject To
Binary
  x0 x1 x2 x3 x4 x5
End 
import sys
import math

for line in sys.stdin:
    line = line.strip()
    if not line: continue
    t, x, y, z = line.split('\t')
    
    # 時刻を秒単位で切り捨ててをタイムラインを作る (例: 14:23:01.420 -> 14:23:01)
    window = t.split('.')[0] 
    
    # ノルム計算
    norm = math.sqrt(float(x)**2 + float(y)**2 + float(z)**2)
    
    # Key: 窓時刻, Value: ノルム
    print(f"{window}\t{norm}")

import sys
from itertools import groupby
from operator import itemgetter

def classify(var):
    #値をもとに状態を解析するための条件分岐
    if var < 0.01: return "STILL"
    elif var < 0.3: return "WALK"
    else: return "RUN"

print(f"{'Time Window':<20} | {'Variance':<10} | {'State'}")
print("-" * 45)

lines = (line.strip().split('\t') for line in sys.stdin if line.strip())
for window, group in groupby(lines, itemgetter(0)):
    norms = [float(val) for key, val in group]
    n = len(norms)
    if n > 1:
        mean = sum(norms) / n
        var = sum((x - mean)**2 for x in norms) / n
        state = classify(var)
        print(f"{window:<20} | {var:.6f} | {state}")

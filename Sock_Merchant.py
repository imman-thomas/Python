#!/bin/python3

import math
import os
import random
import re
import sys

# Complete the sockMerchant function below.
def sockMerchant(n, arr):
    arr.sort()
    d = dict()
    for i in arr:
        if i not in d:
            d[i] = 1
        else :
            d[i] += 1
    counter = 0
    for v in d:
    #    print(d.get(v))
        counter += int(d.get(v)/2)

    return counter
     

if __name__ == '__main__':
    fptr = open(os.environ['OUTPUT_PATH'], 'w')

    n = int(input())

    ar = list(map(int, input().rstrip().split()))

    result = sockMerchant(n, ar)

    fptr.write(str(result) + '\n')

    fptr.close()

#git test

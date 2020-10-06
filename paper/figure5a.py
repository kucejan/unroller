#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import itertools

packets = 100000
Brange = [5]
Lrange = [20]
detections = [1]

genloops = True
genpaths = False
topoloops = False
topopaths = False

enunroller = True
enbloomfilter = False

brange = [4]
cHrange = list(itertools.product([1, 2, 3, 4, 5, 6, 7, 8], [1, 2, 4]))
zrange = [32]

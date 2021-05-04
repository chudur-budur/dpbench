# Copyright (C) 2017-2018 Intel Corporation
#
# SPDX-License-Identifier: MIT

import numpy as np
import numpy.random as rnd
import sys,os

try:
    import itimer as it
    now = it.itime
    get_mops = it.itime_mops_now
except:
    from timeit import default_timer
    now = default_timer
    get_mops = lambda t0, t1, n: (n / (t1 - t0),t1-t0)

######################################################
# GLOBAL DECLARATIONS THAT WILL BE USED IN ALL FILES #
######################################################

# make xrange available in python 3
try:
    xrange
except NameError:
    xrange = range

SEED = 7777777
XL = 1.0
XH = 5.0
dims = 2

NUMBER_OF_CENTROIDS = 10

###############################################
def get_device_selector (is_gpu = True):
    if is_gpu is True:
        device_selector = "gpu"
    else:
        device_selector = "cpu"

    if os.environ.get('SYCL_DEVICE_FILTER') is None or os.environ.get('SYCL_DEVICE_FILTER') == "opencl":
        return "opencl:" + device_selector

    if os.environ.get('SYCL_DEVICE_FILTER') is "level_zero":
        return "level0:" + device_selector

    return os.environ.get('SYCL_DEVICE_FILTER')

def gen_data(nopt):
    return (
        rnd.uniform(XL, XH, (nopt, dims)),
        np.ones(nopt, dtype=np.int32),
        np.ones((NUMBER_OF_CENTROIDS, 2), dtype=np.float64),
        np.ones((NUMBER_OF_CENTROIDS, 2), dtype=np.float64),
        np.ones(NUMBER_OF_CENTROIDS, dtype=np.int32)        
    )

##############################################	

def run(name, alg, sizes=10, step=2, nopt=2**13):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--steps', required=False, default=sizes,  help="Number of steps")
    parser.add_argument('--step',  required=False, default=step,   help="Factor for each step")
    parser.add_argument('--size',  required=False, default=nopt,   help="Initial data size")
    parser.add_argument('--repeat',required=False, default=100,    help="Iterations inside measured region")
    parser.add_argument('--text',  required=False, default="",     help="Print with each result")
    
    args = parser.parse_args()
    sizes= int(args.steps)
    step = int(args.step)
    nopt = int(args.size)
    repeat=int(args.repeat)

    rnd.seed(SEED)
    f=open("perf_output.csv",'w')
    f2 = open("runtimes.csv",'w',1)
    
    for i in xrange(sizes):
        X,arrayPclusters,arrayC,arrayCsum,arrayCnumpoint = gen_data(nopt)
        iterations = xrange(repeat)
        print("ERF: {}: Size: {}".format(name, nopt), end=' ', flush=True)
        sys.stdout.flush()

        alg(X, arrayPclusters,arrayC,arrayCsum,arrayCnumpoint, nopt, NUMBER_OF_CENTROIDS) #warmup
        t0 = now()
        for _ in iterations:
            alg(X, arrayPclusters,arrayC,arrayCsum,arrayCnumpoint, nopt, NUMBER_OF_CENTROIDS)

        mops,time = get_mops(t0, now(), nopt)
        f.write(str(nopt) + "," + str(mops*2*repeat) + "\n")
        f2.write(str(nopt) + "," + str(time) + "\n")
        print("Time:", str(time))
        nopt *= step
        repeat -= step
        if repeat < 1:
            repeat = 1
    f.close()
    f2.close()

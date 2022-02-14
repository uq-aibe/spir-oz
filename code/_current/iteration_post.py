# ======================================================================
#     Created by Josh Aberdeen, Cameron Gordon, Patrick O'Callaghan 11/2021
# ======================================================================

import numpy as np
from parameters import *
from variables import *
from equations import *
import solver_post
# import cPickle as pickle
import pickle
import os

#from numpy.random import PCG64
#from datetime import datetime
import time 
# ======================================================================


#def sceq(i_pth, rng, save_data=True):
def sceq(i_pth, save_data=True):
    # i_pth is greater than zero
    s = i_pth - 1
    Kap(j,s) = unpickle.Kpath(j, s, "0") 
    #solve busc_tipped using nlp maximizing obj;
    solver_post.ipopt_interface(Xtraining[iI], n_agt,verbose=verbose) 
###
                 
        
        if i_pth == 0: 
            res = solver.ipopt_interface(Xtraining[iI], n_agt,initial=True,verbose=verbose)
        else: 
            res = solver_post.ipopt_interface(Xtraining[iI], n_agt,initial=False,verbose=verbose)
        print(res['ITM'])
        SAV_add = np.zeros(n_agt, float)
        ITM_add = np.zeros(n_agt, float)
        for iter in range(n_agt):
            SAV_add[iter] = np.add(res["SAV"][iter*n_agt], res["SAV"][iter*n_agt+1])
            ITM_add[iter] = res["ITM"][iter*n_agt] + res["ITM"][iter*n_agt+1]
        print(ITM_add)
        res['kap'] = Xtraining[iI]
        res['itr'] = i_pth
        y[iI] = res['obj']
        ctt = res['ctt']
        msg = "Constraint values: " + str(ctt) + os.linesep
        msg += "a quick check using output_f - con - SAV_add - ITM_add" + os.linesep
        msg += (
            str(output_f(Xtraining[iI], res["itm"]) - np.add(res['con'], SAV_add, ITM_add)) + os.linesep
        )
        print(ITM_add)
        msg += (
            "and consumption, labor, investment and intermediate inputs are, respectively,"
            + os.linesep
            + str(res['con'])
            #+ os.linesep
            #+ str(res['lab'])
            + os.linesep
            + str(res['SAV'])
            + str(res['sav'])
            + str(SAV_add)
            + os.linesep
            + str(res['ITM'])
            + str(res['itm'])
            + str(ITM_add)
        )
        if economic_verbose:
            print("{}".format(msg))
        if i_pth == numits - 1:
            ctnr.append(res)
    end_nlp = time.time()


    elif i_pth > 0: 
        # Load the model from the previous i_pth step
        restart_data = filename + str(i_pth - 1) + ".pcl"
        with open(restart_data, "rb") as fd_old:
            gp_old = pickle.load(fd_old)
            print("data from i_pth step ", i_pth - 1, "loaded from disk")
        fd_old.close()

    
    y = np.zeros(No_samples, float)  # training targets

    ctnr = []
    # solve bellman equations at training points
    # Xtraining is our initial level of capital for this i_pth

    # print data for debugging purposes
    # for iI in range(len(Xtraining)):
    # print Xtraining[iI], y[iI]
    # Instantiate a Gaussian Process model
    # kernel = 1.0 * RBF(length_scale=1.0, length_scale_bounds=(1e-1, 10.0))

    # kernel = 1.0 * RBF(length_scale=100.0, length_scale_bounds=(1e-1, 2e2)) \
    # + WhiteKernel(noise_level=1, noise_level_bounds=(1e-3, 1e+0))

    # kernel = 1.0 * RBF(length_scale=100.0, length_scale_bounds=(1e-1, 2e2))
    # kernel = 1.0 * Matern(length_scale=1.0, length_scale_bounds=(1e-1, 10.0),nu=1.5)
    stt_gpr = time.time()
    gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=n_restarts_optimizer, alpha=alphaSK)
    end_gpr = time.time()
    # Fit to data using Maximum Likelihood Estimation of the parameters
    gp.fit(Xtraining, y)

    ##save the model to a file
    output_file = filename + str(i_pth) + ".pcl"
    print(output_file)
    with open(output_file, "wb") as fd:
        pickle.dump(gp, fd, protocol=pickle.HIGHEST_PROTOCOL)
        print("data of step ", i_pth, "  written to disk")
        print(" -------------------------------------------")
    fd.close()

    if i_pth == numits - 1:
        return ctnr


# ======================================================================

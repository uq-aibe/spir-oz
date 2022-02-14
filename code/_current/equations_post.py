# ======================================================================
#     Created by Josh Aberdeen, Cameron Gordon, Patrick O'Callaghan 11/2021
# ======================================================================

from cmath import sqrt
import numpy as np
from parameters import *
from variables import * 

# ======================================================================
# utility function u(c,l)
def utility(con, lab):
    return sum(np.log(con))  # + sum(lab) # -J could make cobb-douglas, may fix /0 issue
### CJ has power with gamma similar to Scheidegger

# ======================================================================
# initial guess of the value function v(k)
def V_INFINITY(kap=[]):
    e = np.ones(len(kap))
    c = output_f(kap, kap / 3)
    v_infinity = utility(c) / (1 - beta)
    return v_infinity


# ======================================================================
# output_f
def output(zeta, k, l):
    return zeta2*A*(k[:,t]**alpha) * (l[:,t]**(1-alpha))


# ======================================================================
# value function
def value(init, gp_old, Kap2):
    if init:
        return V_INFINITY(Kap2)
    else:
        return gp_old.predict(Kap2, return_std=True)[1]

# ======================================================================
# adjustment costs for investment 
def Gamma_adjust(kap=[], inv=[]):
    fun_val = 0.5*phi*kap*((inv/kap - delta)**2.0) #CJ change zeta to phi
    return fun_val

# ======================================================================
# budget constraint
def budget(c,Inv,k,A,l,t, Probs, untipped):
    return sum(c[:,t] + Inv[:,t] + Gamma_adjust(k, Inv)) - sum(output(etc, untipped))
    
# ======================================================================
# v-tail

V_tail = sum(tau[j] * beta**DT*((( (0.75*A*(k(j,s + Delta_s)**phik * 1))**gammahat )/gammahat - B * 1)/(1-beta)) for j in range(1:n_agts))

# ======================================================================
# Constraints

def f_ctt(X, gp_old, Kap2, init, kap):
    # f_prod=output_f(kap, lab, itm)
    e_ctt = dict()
    # canonical market clearing constraint
    # e_ctt["mclt"] = X[I["con"]] + SAV_add + ITM_add - X[I["out"]] ## for Cai-Judd rep
    e_ctt["mclt"] = budget(X[I["con"]],X[I["sav"]])
    # capital next period constraint
    e_ctt["knxt"] = (1 - delta) * kap + X[I["sav"]] - X[I["knx"]]  ### Gamma to go here
#    # intermediate sum constraints
    e_ctt["savt"] = SAV_com - X[I["sav"]]
    # e_ctt["itmt"] = ITM_com - X[I["itm"]] ## for Cai-Judd rep
    # value function constraint
 #   e_ctt["valt"] = X[I["val"]] - sum(value_f(init, gp_old, Kap2))
    # output constraint
    e_ctt["outt"] = X[I["out"]] - output(kap, X[I["itm"]])  # *np.power(lab, phil)
    # utility constraint
    e_ctt["utlt"] = X[I["utl"]] - utility(X[I["con"]])
    # e_ctt["blah blah blah"] = constraint rearranged into form that can be equated to zero

    # Check dicts are all same length
    if not len(d_ctt) == len(ctt_U) == len(ctt_L) == len(e_ctt):
        raise ValueError(
            "Constraint-related Dicts are not all the same length, check f_cct in parameters.py"
        )

    return e_ctt

        # Summing the 2d policy variables
    # SAV_com = np.ones(n_agt, float)
    # SAV_add = np.zeros(n_agt, float)
    # ITM_com = np.ones(n_agt, float)
    # ITM_add = np.zeros(n_agt, float)
    # for iter in range(n_agt):
    #     for ring in range(n_agt):
    #         #  SAV_com[iter] *= X[I["SAV"]][iter+n_agt*ring]**xi[ring] ## for Cai-Judd rep
    #         #  ITM_com[iter] *= X[I["ITM"]][iter+n_agt*ring]**mu[ring] ## for Cai-Judd rep
    #         #  SAV_add[iter] += X[I["SAV"]][iter*n_agt+ring] ## for Cai-Judd rep
    #         #SAV_add[iter] += X[I["SAV"]][iter * n_agt + ring]  ### to add Gamma?
    #     #  ITM_add[iter] += X[I["ITM"]][iter*n_agt+ring] ## for Cai-Judd rep

def f_ctt_post(X, gp_old, Kap2, init, kap):
    # f_prod=output_f(kap, lab, itm)
    e_ctt = dict()
    # canonical market clearing constraint
    # e_ctt["mclt"] = X[I["con"]] + SAV_add + ITM_add - X[I["out"]] ## for Cai-Judd rep
    e_ctt["mclt"] = budget(X[I["con"]],X[I["sav"]], etc, 1)
    # capital next period constraint
    e_ctt["knxt"] = (1 - delta) * kap + X[I["sav"]] - X[I["knx"]]  ### Gamma to go here
#    # intermediate sum constraints
    e_ctt["savt"] = SAV_com - X[I["sav"]]
    # e_ctt["itmt"] = ITM_com - X[I["itm"]] ## for Cai-Judd rep
    # value function constraint
 #   e_ctt["valt"] = X[I["val"]] - sum(value_f(init, gp_old, Kap2))
    # output constraint
    e_ctt["outt"] = X[I["out"]] - output(kap, X[I["itm"]])  # *np.power(lab, phil)
    # utility constraint
    e_ctt["utlt"] = X[I["utl"]] - utility(X[I["con"]])
    # e_ctt["blah blah blah"] = constraint rearranged into form that can be equated to zero

    # Check dicts are all same length
    if not len(d_ctt) == len(ctt_U) == len(ctt_L) == len(e_ctt):
        raise ValueError(
            "Constraint-related Dicts are not all the same length, check f_cct in parameters.py"
        )

    return e_ctt
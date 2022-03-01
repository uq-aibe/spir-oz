from jax.config import config
config.update("jax_enable_x64", True)

import jax.numpy as np
from jax import jit, grad, jacrev, jacfwd
from cyipopt import minimize_ipopt
#==============================================================================
#-------------economic parameters
#-----------basic economic parameters
NREG = 4        # number of regions
NSEC = 6        # number of sectors
PHZN = LFWD = 10# look-forward parameter / planning (time) horizon (Delta_s)
NPOL = 3        # number of policy types: con, lab, knx, #itm
NITR = LPTH = 28# path length (Tstar): number of random steps along given path
NPTH = 1        # number of paths (in basic example Tstar + 1)
BETA = 99e-2    # discount factor
ZETA0 = 1       # output multiplier in status quo state 0
ZETA1 = 95e-2   # output multiplier in tipped state 1
PHIA = 5e-1     # adjustment cost multiplier
PHIK = 5e-1     # weight of capital in production # alpha in CJ
TPT = 1e-2      # transition probability of tipping (from state 0 to 1)
GAMMA = 5e-1    # power utility exponent
DELTA = 25e-3   # depreciation rate
ETA = 5e-1      # Frisch elasticity of labour supply
RHO = np.ones(NREG) # regional weights (population)
TCS=75e-2       # Tail Consumption Share
#-----------suppressed basic parameters
#PHIM = 5e-1    # weight of intermediate inputs in production
#XI = np.ones(NRxS) * 1 / NRxS # importance of kapital input to another
#MU = np.ones(NRxS) * 1 / NRxS # importance of one sector to another
#-----------derived economic parameters
NRxS = NREG * NSEC
NVAR = NPOL * LFWD * NSEC * NREG    # total number of variables
IVAR = np.arange(0,NVAR)    # index set (as np.array) for all variables
GAMMAhat = 1 - 1 / GAMMA    # utility parameter (consumption denominator)
ETAhat = 1 + 1 / ETA        # utility parameter
PHIL = 1 - PHIK             # labour's importance in production
DPT = (1 - (1 - DELTA) * BETA) / (PHIK * BETA) # deterministic prod trend
RWU = (1 - PHIK) * A * (A - DELTA) ** (-1 / GAMMA) # rel weight: c vs l in u
ZETA = np.array([ZETA0, ZETA1])

#==============================================================================
#-----------structure of x using latex notation:
#---x = [
#        x_{p0, t0, r0, s0}, x_{p0, t0, r0, s1}, x_{p0, t0, r0, s2},
#
#        x_{p0, t0, r1, s0}, x_{p0, t0, r1, s1}, x_{p0, t0, r1, s2},
#
#        x_{p0, t1, r0, s0}, x_{p0, t1, r0, s1}, x_{p0, t1, r0, s2},
#
#        x_{p0, t1, r1, s0}, x_{p0, t1, r1, s1}, x_{p0, t1, r1, s2},
#
#        x_{p1, t0, r0, s0}, x_{p1, t0, r0, s1}, x_{p0, t0, r0, s2},
#
#        x_{p1, t0, r1, s0}, x_{p1, t0, r1, s1}, x_{p0, t0, r1, s2},
#
#        x_{p1, t1, r0, s0}, x_{p1, t1, r0, s1}, x_{p0, t1, r0, s2},
#
#        x_{p1, t1, r1, s0}, x_{p1, t1, r1, s1}, x_{p0, t1, r1, s2},
#
#
#        x_{p2, t0, r0, s00}, x_{p2, t0, r0, s01}, x_{p2, t0, r0, s02},
#        x_{p2, t0, r0, s10}, x_{p2, t0, r0, s11}, x_{p2, t0, r0, s12},
#        x_{p2, t0, r0, s20}, x_{p2, t0, r0, s21}, x_{p2, t0, r0, s22},
#
#        x_{p2, t0, r1, s00}, x_{p2, t0, r1, s01}, x_{p2, t0, r1, s02},
#        x_{p2, t0, r1, s10}, x_{p2, t0, r1, s11}, x_{p2, t0, r1, s12},
#        x_{p2, t0, r1, s20}, x_{p2, t0, r1, s21}, x_{p2, t0, r1, s22},
#
#        x_{p2, t1, r0, s00}, x_{p2, t1, r0, s01}, x_{p2, t1, r0, s02},
#        x_{p2, t1, r0, s10}, x_{p2, t1, r0, s11}, x_{p2, t1, r0, s12},
#        x_{p2, t1, r0, s20}, x_{p2, t1, r0, s21}, x_{p2, t1, r0, s22},
#
#        x_{p2, t1, r1, s00}, x_{p2, t1, r1, s01}, x_{p2, t1, r1, s02},
#        x_{p2, t1, r1, s10}, x_{p2, t1, r1, s11}, x_{p2, t1, r1, s12},
#        x_{p2, t1, r1, s20}, x_{p2, t1, r1, s21}, x_{p2, t1, r1, s22},
#
#
#        x_{p3, t0, r0, s00}, x_{p3, t0, r0, s01}, x_{p3, t0, r0, s02},
#        x_{p3, t0, r0, s10}, x_{p3, t0, r0, s11}, x_{p3, t0, r0, s12},
#        x_{p3, t0, r0, s20}, x_{p3, t0, r0, s21}, x_{p3, t0, r0, s22},
#
#        x_{p3, t0, r1, s00}, x_{p3, t0, r1, s01}, x_{p3, t0, r1, s02},
#        x_{p3, t0, r1, s10}, x_{p3, t0, r1, s11}, x_{p3, t0, r1, s12},
#        x_{p3, t0, r1, s20}, x_{p3, t0, r1, s21}, x_{p3, t0, r1, s22},
#
#        x_{p3, t1, r0, s00}, x_{p3, t1, r0, s01}, x_{p3, t1, r0, s02},
#        x_{p3, t1, r0, s10}, x_{p3, t1, r0, s11}, x_{p3, t1, r0, s12},
#        x_{p3, t1, r0, s20}, x_{p3, t1, r0, s21}, x_{p3, t1, r0, s22},
#
#        x_{p3, t1, r1, s00}, x_{p3, t1, r1, s01}, x_{p3, t1, r1, s02},
#        x_{p3, t1, r1, s10}, x_{p3, t1, r1, s11}, x_{p3, t1, r1, s12},
#        x_{p3, t1, r1, s20}, x_{p3, t1, r1, s21}, x_{p3, t1, r1, s22},
#       ]
#
#==============================================================================
#-----------dicts of index lists for locating variables in x:
#-------Dict for locating every variable for a given policy
d_pol_ind_x = dict()
for p in polNames:
    d_pol_ind_x[p] = range(len(x))[
          NSEC ** d_dim[p] * NREG * PHZN * i_pol[p]
        : NSEC ** d_dim[p] * NREG * PHZN * (i_pol[p] + 1)
        : 1]

#-------Dict for locating every variable at a given time
d_tim_ind_x = dict()
for t in range(PHZN):
    indlist = []
    for p in polNames:
        indlist += range(len(x))[
             NSEC ** d_dim[p] * NREG * (i_pol[p] * PHZN + t)
           : NSEC ** d_dim[p] * NREG * (i_pol[p] * PHZN + t + 1)
           : 1]
    d_tim_ind_x[t] = sorted(indlist)

#-----------the final one can be done with a slicer with stride NREG
#-------Dict for locating every variable in a given region
d_reg_ind_x = dict()
for r in regNames:
    indlist = []
    for t in range(PHZN):
        for p in polNames:
            indlist += range(len(x))[
                  NSEC ** d_dim[p] * (p * NREG * PHZN + t * NREG + r)
                : NSEC ** d_dim[p] * (p * NREG * PHZN + t * NREG + r + 1)
                : 1]
    d_reg_ind_x[r] = sorted(indlist)

#-------Dict for locating every variable in a given sector
d_sec_ind_x = dict()
for s in sectNames: #comment
    indlist = []
    for t in range(PHZN):
        for p in polNames:
            indlist += range(len(x))[
                  NSEC ** d_dim[p] * (p * NREG * PHZN + t * NREG + r) + s
                : NSEC ** d_dim[p] * (p * NREG * PHZN + t * NREG + r) + s + 1
                : 1]
    d_sec_ind_x[s] = sorted(indlist)
#-----------union of all the "in_x" dicts: those relating to indices of x
d_ind_x = d_pol_ind_x | d_tim_ind_x | d_reg_ind_x | d_sec_ind_x

#==============================================================================
#-----------function for intersecting two lists: returns indices as np.array
def f_I2L(list1,list2):
    return np.array(list(set(list1) & set(list2)))

#-----------function for returning index subsets of x for a pair of dict keys
def sub_ind_x(key1,             # any key of d_ind_x
              key2,             # any key of d_ind_x
              d=cpar.d_ind_x,   # dict of index categories: pol, time, sec, reg
              ):
    val = np.array(list(set(d['key1']) & set(d['key2'])))
    return val

#==============================================================================
#-----------computational parameters
#dI_CON = dict()
#dI_LAB = dict()
#dI_KNX = dict()
#for t in range(LFWD):
#    dI_CON[t] = f_I2L(dI_P["con"], dI_T[t]) # Index set of con
#    dI_LAB[t] = f_I2L(dI_P["lab"], dI_T[t]) # Index set of lab
#    dI_KNX[t] = f_I2L(dI_P["knx"], dI_T[t]) # Index set of knx
#I_CON = np.array(dI_P["con"])]
#I_LAB = np.array(dI_P["lab"])]
#I_FNLKNX = f_I2L(dI_P["knx"], dI_T[PHZN])  # Index set for final knx in plan

#==============================================================================
#-----------objective function (purified)
def objective(x,                    # full vector of variables
              beta=par.BETA,        # discount factor
              phzn=par.PHZN,        # look-forward parameter
              u=efcn.instant_utility# utility function representing flow per t
              v=efcn.V_tail         # tail-sum value function
              ind=cfcn.sub_ind_x    # subindices function for x: req. two keys
              ):
    # extract/locate knx at the planning horizon in x
    kap_phzn = x[ind("knx", phzn)]
    # sum discounted utility over the planning horizon
    sum_disc_utl = 0.0
    for t in range(phzn):
        con_t = x[ind("con", t)]    # locate consumption at t in x
        lab_t = x[ind("lab", t)]    # locate labour at t in x
        sum_disc_utl += beta ** t * u(con_t, lab_t)
    val = sum_disc_utl + beta ** lfwd * v(kap_phzn)
    return val

#==============================================================================
#-----------equality constraints
def eq_constraints(x,
                   state,
                   n_ctt=par.N_CTT
                   mcl=efcn.market_clearing,
                   ind=cfcn.sub_ind_x
                   ):
    eqns = np.zeros(LFWD)
        # constraint 2
    for t in range(LFWD):
        kap_t = state
        knx_t = x[ind("knx", t)]
        con_t = x[ind("con", t)]
        lab_t = x[ind("lab", t)]
        eqns  = eqns.at[i].set(mcl(kap_t, knx_t, con_t, lab_t, t))
    return eqns

#==============================================================================
#-------------build and jit (just-in-time compile) the derivatives
#-----------first the objective
obj = jit(objective)                                        # obj with one arg
obj_grad = jit(grad(obj))                                   # grad
obj_hess = jit(jacrev(jacfwd(obj)))                         # hessian
#-----------then the equality constraints
eq_ctt = jit(lambda x, state: eq_constraints(x, state))     # eq_ctt two-args
eq_ctt_jac = jit(jacfwd(eq_ctt))                            # jacobian
eq_ctt_hess = jacrev(jacfwd(eq_ctt))                        # hessian
#-----------then the inequality constraints
#con_ineq = jit(ineq_constraints)                           # ineq_ctt two-args 
#ineq_ctt_jac = jit(jacfwd(ineq_ctt))                       # jacobian
#ineq_ctt_hess = jacrev(jacfwd(ineq_ctt))                   # hessian
#ineq_ctt_hessvp = jit(lambda x, v: ineq_ctt_hess(x) * v[0])# hessian vec-prod

#==============================================================================
#-----------define the jitted-state-in functions for the loop
def eq_ctt_js(state):
    return lambda x: eq_ctt(x, state)
def eq_ctt_jac_js(state):
    return lambda x: eq_ctt_jac(x, p)
def eq_ctt_hess_js(state):
    return lambda x: eq_ctt_hess(x, state)

#==============================================================================
#-----------variable bounds:
bnds = [(0.1, 100.0) for _ in range(x0.size)]

#==============================================================================
#-*-*-*-*-*-loop/iteration along path starts here 
res = dict()
for s in range(1, LPTH):
    #-------feed in kapital from starting point s-1
    eq_ctt_fin = eq_ctt_js(state=res[s - 1]["x"][ind("knx", 1)])
    eq_ctt_jac_fin = eq_ctt_jac_js(state=d[s])
    eq_ctt_hess_fin = eq_ctt_hess_js(state=d[s])
    #!!-----create and jit the hessian vector product-more explanation needed!!
    eq_ctt_hessvp = jit(lambda x, v: eq_ctt_hess(x) * v[0]) # hessian vec-prod
    #-------wrap up constraints for cyipopt
    cons = [{'type': 'eq',
             'fun': eq_ctt_fin,
             'jac': eq_ctt_jac,
             'hess': eq_ctt_hessvp,
             }]
    #-----------starting point (absent warm start)
    x0 = np.array([15.0, 14.0, 13.0, 12.0])

    #-----------execute solver
    res[s] = minimize_ipopt(obj,
                            jac=obj_grad,
                            hess=obj_hess,
                            x0=x0,
                            bounds=bnds,
                            constraints=cons,
                            options={'disp': 1, # printout range:0-12, default=5
                                     'obj_scaling_factor': -1.0, # maximize obj
                                     'timing_statistics': 'yes',
                                     'print_timing_statistics': 'yes',
                                     #!!how to warm start? see ipopt options page!!
                                     #'warm_start_init_point': 'yes', 
                                     #!!next one for "multiple problems in one nlp"!!
                                     #'warm_start_same_structure': 'yes',
                                     }
                            )
#-*-*-*-*-*-loop ends here

#==============================================================================
# ----------- print solution, etc.
for s in range(len(res)):
    print("the solution for iterate ", s, "is ", res[s])
    x_sol[s] = res[s]["x"]
    print("sol=", x_sol[s])
    for i in range(len(x_sol[s])-1):
        print("diff=", x_sol[s][i] - x_sol[s][i+1])

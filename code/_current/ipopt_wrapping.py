# ======================================================================
#     Created by Josh Aberdeen, Cameron Gordon, Patrick O'Callaghan 11/2021
# ======================================================================


from parameters import *
from variables import *
import equations

import numpy as np
#mport jax.numpy as jnp
#from jax import jit, grad, jacfwd
from cyipopt import minimize_ipopt

#=======================================================================
#   Objective Function to start VFI (in our case, the value function)
        
def EV_F(X, kap):
    # extract tail kapital
    var_final = X[(Delta - 1) * sum(n_agt**d_ctt[iter]): Delta * sum(n_agt**d_ctt[iter])] 
    kap_tail = var_final[I["knx"]]
    # extract utilities 
    var = []
    for t in range(Delta):
      var[t] = X[(t - 1) * sum(n_agt**d_ctt[iter]): t * sum(n_agt**d_ctt[iter])]
    
    return sum(var[t][I["utl"]] for t in range(Delta)) + beta**Delta * equations.V_tail(kap_tail)

#=======================================================================
    
#=======================================================================
#   Computation of gradient (first order finite difference) of initial objective function 

def EV_GRAD_F(X, kap):
    
    N=len(X)
    GRAD=np.zeros(N, float) # Initial Gradient of Objective Function
    h=1e-4
    
    for ixN in range(N):
        xAdj=np.copy(X)
        
        if (xAdj[ixN] - h >= 0):
            xAdj[ixN]=X[ixN] + h            
            fx2=EV_F(xAdj, kap)
            
            xAdj[ixN]=X[ixN] - h
            fx1=EV_F(xAdj, kap)
            
            GRAD[ixN]=(fx2-fx1)/(2.0*h)
            
        else:
            xAdj[ixN]=X[ixN] + h
            fx2=EV_F(xAdj, kap)
            
            xAdj[ixN]=X[ixN]
            fx1=EV_F(xAdj, kap)
            GRAD[ixN]=(fx2-fx1)/h
            
    return GRAD
    
#=======================================================================
       
#======================================================================
#   Equality constraints for the first time step of the model
      
def EV_G(X, kap):
    M=n_ctt * Delta
    G=np.empty(M, float)

    # I[iter] = slice(prv_ind, prv_ind + n_agt**d_pol[iter])
    # I_ctt[iter] = slice(prv_ind, prv_ind + n_agt**d_ctt[iter])
    var = []
    e_ctt = dict()
    for t in range(Delta):
        for iter in ctt_key:
            var[t] = X[t * sum(n_agt**d_ctt[iter]): (t+1) * sum(n_agt**d_ctt[iter])]
        # pull in constraints
        e_ctt[t] = equations.f_ctt(var[t], kap, t)
        # apply all constraints with this one loop
        for iter in ctt_key:
            G[I_ctt[iter]] = e_ctt[t][iter]

    return G

#======================================================================

#======================================================================
#   Computation (finite difference) of Jacobian of equality constraints 
#   for first time step
    
def EV_JAC_G(X, flag, kap):
    N=n_pol
    M=n_ctt
    #print(N, "  ",M) #testing testing
    NZ=n_pol*n_ctt 
    A=np.empty(NZ, float)
    ACON=np.empty(NZ, int) # its cause int is already a global variable cause i made it
    AVAR=np.empty(NZ, int)    
    
    # Jacobian matrix structure
    
    if (flag):
        for ixM in range(M):
            for ixN in range(N):
                ACON[ixN + (ixM)*N]=ixM
                AVAR[ixN + (ixM)*N]=ixN
                
        return (ACON, AVAR)
        
    else:
        # Finite Differences
        h=1e-4
        gx1=EV_G(X, kap)
        
        for ixM in range(M):
            for ixN in range(N):
                xAdj=np.copy(X)
                xAdj[ixN]=xAdj[ixN]+h
                gx2=EV_G(xAdj, kap, n_agt)
                A[ixN + ixM*N]=(gx2[ixM] - gx1[ixM])/h
        return A
  
#======================================================================

#======================================================================

class cyipopt_class_inst: 
    """
    Class for the optimization problem to be passed to cyipopt 
    Further optimisations may be possible here by including a hessian (optional param)
    """
    def __init__(self, X, n_prim, k_init, NELE_JAC, NELE_HESS=None, verbose=True): 
        self.x = X 
        self.n_polDel = n_prim
        self.k_init = k_init 
        self.NELE_JAC = NELE_JAC 
        self.NELE_HESS = NELE_HESS
        self.verbose = verbose

    # Create ev_f, eval_f, eval_grad_f, eval_g, eval_jac_g for given k_init and n_agent 
    def eval_f(self, x): 
        return EV_F(x, self.k_init)

    def eval_grad_f(self, x): 
        return EV_GRAD_F(x, self.k_init)  
        
    def eval_g(self, x):
        return EV_G(x, self.k_init)
        
    def eval_jac_g(self, x, flag):
        return EV_JAC_G(x, self.k_init, flag)

    def objective(self, x): 
        # Returns the scalar value of the objective given x. 
        return self.eval_f(x) 

    def gradient(self, x): 
        # Returns the gradient fo the objective with respect to x.""" 
        return self.eval_grad_f(x) 

    def constraints(self, x): 
        # Returns the constraints 
        return self.eval_g(x) 

    def jacobian(self, x): 
        # Returns the Jacobian of the constraints with respect to x. 
        return self.eval_jac_g(x, False) 

    def intermediate(self, alg_mod, iter_count, obj_value, inf_pr, inf_du, mu,
                     d_norm, regularization_size, alpha_du, alpha_pr,
                     ls_trials):
        """Prints information at every Ipopt i_pth."""

        if self.verbose: 
            msg = "Objective value at step #{:d} of current optimization is - {:g}"
            print(msg.format(iter_count, obj_value))

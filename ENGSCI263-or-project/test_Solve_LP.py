# contains tests for Solve_LP.py

import numpy as np
from Solve_LP import *
from numpy.linalg import norm

# for clear printouts
from termcolor import colored    


def test_solve_lp():
    ''' This function tests solve_lp for different inputs and prints test results to screen

        Parameters:
        -----------
        None

        Returns:
        --------
        None

        Notes:
        ------
        Red text printing to screen indicates a test failure.
        Green text indicates test passing.
        Blue text denotes function outputs for a particular test.
        This only works for the general implementation of Solve_LP
        and not later versions where overtime is costed.
    '''

    routes_1 = np.array([
        [1, 0, 0, 1, 0, 0, 5, 0],
        [0, 1, 0, 0, 0, 1, 8, 0],
        [0, 0, 1, 1, 0, 0, 2, 0],
        [1, 0, 0, 0, 1, 0, 8, 0],
    ])

    routes_2 = np.array([
        [1, 0, 0, 1, 0],
        [0, 1, 0, 1, 0],
        [0, 0, 1, 1, 0]
    ])

    routes_3 = np.array([
        [1, 0, 0, 10, 0],
        [0, 1, 0, 10, 0],
        [0, 0, 1, 10, 0],
        [1, 0, 0, 1, 0],
        [0, 1, 0, 1, 0],
        [0, 0, 1, 1, 0],
    ])

    routes = []
    routes.append(routes_1)
    routes.append(routes_2)
    routes.append(routes_3)

    # actual solutions to VRP's above
    costs=np.array([18,3,3])
    routes_names_solns = [
        ['Route_1','Route_2','Route_3'],
        ['Route_0','Route_1','Route_2'],
        ['Route_3','Route_4','Route_5']
    ]

    # test routes_n
    j=0
    for i in range(len(routes)): 
        try:
            best_routes, cost=solve_lp(routes[i])
            # store only strings of the routes
            best_routes_names=[]
            [best_routes_names.append(route.name) for route in best_routes]
            assert(best_routes_names==routes_names_solns[i])
            assert(norm(cost - costs[i]) <0.0001)
            print(colored("Routes_{:d} TEST PASS", 'green').format(i))
            # track how many pass
            j+=1
        except(AssertionError):
            print(colored("Routes_{:d} TEST FAIL", 'red').format(i))
    
    print(colored('Number passed : {:d}', 'green').format(j))
    print(colored('Number failed : {:d}', 'red').format(i+1-j))


if __name__ == "__main__":
    test_solve_lp()

    


    
import numpy as np
import pandas as pd 
from pulp import *
from Generate_Routes import *

# example input:
'''
n=2
# make a random input array of 1's and 0's
routes_input = np.concatenate([np.ones(shape=(n,5)), np.zeros(shape=(n,5))], axis=1)
for i in range(np.size(routes_input,0)):
    routes_input[i,:] = np.random.permutation(routes_input[i,:])
# add the costs
routes_input = np.concatenate([routes_input, np.transpose([np.arange(n)])], axis=1)
# add supply - all from north
routes_input=np.concatenate([routes_input, np.transpose([np.ones(n)])], axis=1)
'''

# course book example p13, Topic 2:
routes_input = np.array([
    [1, 0, 0, 1, 0, 0, 5, 0],
    [0, 1, 0, 0, 0, 1, 8, 0],
    [0, 0, 1, 1, 0, 0, 2, 0],
    [1, 0, 0, 0, 1, 0, 8, 0],
])

#To Do list:
# what is the format of routes?
# get the cost of each route and store in cost[i]
# what is the convention if the node isnt included in our route (we suggest -1).

def solve_lp(routes_input, Saturday=False):
    ''' Solves a vehicle routing problem given some routes and costs

        Parameters:
        -----------
        routes_input : array-like
            Stores the nodes visited by each route and the cost of each
        Saturday : bool (optional)
            Removes some constraints for solving problem on Saturdays - since no demand at some stores

        Returns:
        --------
        best_routes : vector
            The routes which give the lowest total travel time
        cost : float
            The minimum travel time for these routes


        Notes:
        ------
        routes_input must have each route as a row of 1's and 0's.
        The second-to-last column must contain the cost of the routes.
        The final column contains the supply information - true for north supply,
        false for south supply.
        Saturday should be set to true to exclude Noel Leeming stores on Saturdays 
        from solution.
    '''

    # create array of routes - to use as decision variables
    Routes = []
    [Routes.append("{:d}".format(i)) for i in range(np.size(routes_input,0))] #- number of rows same as input rows 

    # make a list of node names only 
    node_names=["Node_{:d}".format(i) for i in range(np.size(routes_input,1))]

    # Pandas DataFrame construction
    # by convention, cost encoded as 2nd to last input of Routes
    cost = routes_input[:,-2]

    # convert the cost to pd.Series
    Cost = pd.Series(cost, index=Routes)

    # dictionary of match_rhs created:
    # we need the same no. of '=1' RHS as there are nodes in the network. If it is Saturday, then the first 20
    # nodes are closed so will be required to be '=0'.
    match_rhs={}
    for i in range(np.size(routes_input,1)):
        if Saturday:
            if i < 21:
                match_rhs.update({"Node_{:d}".format(i): 0})
            else:
                match_rhs.update({"Node_{:d}".format(i): 1})
        else:
            match_rhs.update({"Node_{:d}".format(i): 1})

    route_vars = LpVariable.dicts("Route", Routes, 0, None, LpInteger)

    prob = LpProblem("Route_Solver_Problem", LpMinimize)
    # convert cost to $/h here

    # must charge 175*4h for first 4h
    # extra cost for going over 4h
    prob += lpSum([(175/3600)*14400*route_vars[i]+(250/3600)*(Cost[i]-14400)*route_vars[i] if(Cost[i]>14400) else (175/3600)*Cost[i]*route_vars[i] for i in Routes])
    
    #prob += lpSum([(175/3600)*Cost[i]*route_vars[i] for i in Routes])
    
    # add part of obj for routes >4h:
    #prob += lpSum([(175/3600)*14400*route_vars[i] for i in Routes if (Cost[i]> 14400)]) # must charge 175*4h for first 4h
    #prob += lpSum([(250/3600)*(Cost[i]-14400) for i in Routes if (Cost[i]>14400)]) # extra cost for going over 4h

    # Making pd.Series - one for each node - containing which routes
    # pass through that node & storing all these in a pd.DataFrame.
    # Have a nested for loop which matches RHS keys to each other and if they match
    # add the constraint to the problem: 

    nodes = [] # store pd.Series here
    for i in range(np.size(routes_input,1)-2):
        node_routes = routes_input[:,i] # get the routes node is included in
        hold_array = [] # initialise input to pd.Series
        for route in node_routes:
            if (route > 0): # if node is in route, must be +ve integer - by convention
                hold_array.append(1) # if node in route, value =1
            else:
                hold_array.append(0) # else 0 N.B.: cannot be bool

        # turn hold_array into pd.Series
        hold_series = pd.Series(hold_array, index=Routes)
        # store
        nodes.append(hold_series)

    # initialise dictionary for routes
    series_names = {node_name : node for node_name,node in zip(node_names,nodes)}


    # initialise data frame 
    NodeRHS = pd.DataFrame(series_names)

    # add these "must visit once" RHS to problem
    # for j in NodeRHS:
    #     prob += lpSum([NodeRHS[j][k]*route_vars[k] for k in Routes]) == 1
    
        # add these "must visit once" RHS to problem
    for i in match_rhs:
        for j in NodeRHS:
            if (i==j): # only add constraint if data and variable names match
                prob += lpSum([NodeRHS[j][k]*route_vars[k] for k in Routes]) == match_rhs[i]

    # hard-coded GUB for total number of trucks
    prob += lpSum([route_vars[i] for i in Routes]) <= 50 # cannot have more than 50 routes chosen

    prob.solve()

    # get routes
    best_routes = []
    for v in prob.variables():
        if(v.varValue==1):
            best_routes.append(v)

    # get total cost
    cost = value(prob.objective)
    return best_routes, cost


def get_path(best_routes, routes_input):
    ''' Returns an array of the least cost paths with the store names as entries
        
        Parameters:
        -----------
        best_routes : array-like
            Lists the routes in the form 'Route_n' as LpVariables
        routes_input : array-like
            Stores the nodes visited by each route and the cost of each

        Returns:
        --------
        route_paths :array-like
            List of store names, in order of visit, for each route
        
        Notes:
        ------ 
    '''

    # get list of stores

    # Load in our string names
    data = np.genfromtxt('demandDataUpdated.csv', skip_header=1, delimiter=',', dtype=None)

    # Extract the list of names of stores, in the correct order - as dictated by demand 
    # dictionary
    names = []
    for line in data:
        line = list(line)
        names.append(line[0].decode('utf-8'))

    # key for taking second element for store name -order pair
    def takeSecond(elem):
        return elem[1]
    
    # match best routes to which stores are included
    route_paths=[]
    for route_n in best_routes:
        route_n_path = []

        # first six characters are 'Route_' -ignore these
        row_no = int(route_n.name[6:])
        row_to_search = routes_input[row_no,:]
        for i in range(len(names)):
            if (row_to_search[i]>0):
                # store the store name and the order in the path 
                route_n_path.append([names[i],row_to_search[i]])
        
        # sort store names by order visited
        route_n_path.sort(key=takeSecond)
        # store only the store names
        store_names=[]
        [store_names.append(path[0]) for path in route_n_path]
        route_paths.append(store_names)

    return route_paths







if __name__ == "__main__":

    regions = region_divide()
    routes_input = all_routes(regions, North_Closed=False, Saturday=False)
    best_routes, cost=solve_lp(routes_input, Saturday=False)
    print(best_routes, len(best_routes),cost)
    #route_paths = get_path(best_routes, routes_input)
    #print(route_paths) 


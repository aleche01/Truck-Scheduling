from Generate_Routes import *
from Solve_LP import *
import pandas as pd
from fitter import Fitter
import matplotlib.pyplot as plt

def traffic():
    # Read in the distances and times between each store into a double dictionary
    time_data = np.genfromtxt('WarehouseDurations.csv', skip_header=1, delimiter=',', dtype=None)
    names = []
    for line in time_data:
        line = list(line)
        names.append(line[0].decode('utf-8'))

    wkday_times = []
    sat_times = []

    for line in time_data:
        line = list(line)
        times = line[1:]

        # Overall variation on Weekdays
        big_var = np.random.uniform(low=1.3, high = 1.5)
        # Overall variation on Saturdays
        big_var_sat = np.random.uniform(low=1.1, high = 1.3)
        # Individual variation (random variation)
        small_var = np.random.uniform(low = 0.85, high = 1.15, size = (42,))

        wkday_times.append({names[i]: (times[i]*big_var*small_var[i]) for i in range(len(names))})
        sat_times.append({names[i]: (times[i]*big_var_sat*small_var[i]) for i in range(len(names))})

    # Convert into dictionary form
    wkdayTimes = {names[i]: wkday_times[i] for i in range(len(names))}
    saturdayTimes = {names[i]: sat_times[i] for i in range(len(names))}

    return wkdayTimes, saturdayTimes


def demand(Saturday = False):
    ''' Simulates variations in our averaged demand values using a bootstrap method

        Returns:
        --------
        best_routes : array-like
            Lists the routes in the form 'Route_n' as LpVariables
        routes_input : array-like
            Stores the nodes visited by each route and the cost of each

        Notes:
        ------
        
    '''
    # Read in demand as a pandas df
    demand = pd.read_csv("demandDataUpdated.csv", header=0, index_col=0)
    
    # Separate the Noel Leeming stores from the Warehouse
    noel_leeming = demand.loc[demand.index.str.startswith('Noel Leeming')]

    warehouse = demand.loc[demand.index.str.startswith("The Warehouse")]

    # Finding the column indexes that correspond to the correct days of the week
    Saturdaynums = []
    Weekdaynums = []

    for i in range(1,len(demand.columns)):
        
        if i % 7 == 6:
            continue 

        elif i % 7 == 5:
            Saturdaynums.append(i)

        else:
            Weekdaynums.append(i)

    # Partition the data correctly for the day of the week
    warehouse_sat = warehouse.iloc[:,Saturdaynums]
    warehouse = warehouse.iloc[:,Weekdaynums]
    noel_leeming = noel_leeming.iloc[:,Weekdaynums]

    # Melt the shit
    warehouse_sat = pd.melt(warehouse_sat, var_name = "Date", value_name= "Pallets")
    warehouse = pd.melt(warehouse, var_name = "Date", value_name= "Pallets")
    noel_leeming = pd.melt(noel_leeming, var_name = "Date", value_name= "Pallets")

    # Create a random selection of demands
    if Saturday:
        data = warehouse_sat["Pallets"]
        sample = data.sample(n = 20, replace = True)

        d = [0] * 20 + sample.values.tolist()

    else:
        warehouse_sample = warehouse["Pallets"].sample(n=20, replace = True)
        noel_sample = warehouse["Pallets"].sample(n=20, replace = True)

        d = noel_sample.values.tolist() + warehouse_sample.values.tolist()

    # Convert list to dictionary
    d_dict = {demand.index[i] : d[i] for i in range(40)}
        
    return d_dict


def bonus_truck(route_paths, best_routes, routes_input, Demand, Times, regions,North_Closed=False):
    ''' Returns routes for the case where nodes in some clusters have unmet demand.

        Parameters:
        -----------
        route_paths :array-like
            List of store names, in order of visit, for each route
        best_routes : array-like
            Lists the routes in the form 'Route_n' as LpVariables
        routes_input : array-like
            Stores the nodes visited by each route and the cost of each
        regions : array-like
            Stores the clusters the nodes are in
        North_Closed : bool
            True if North supply closed, false otherwise

        Returns:
        --------
        best_routes : array-like
            Lists the routes in the form 'Route_n' as LpVariables
        routes_input : array-like
            Stores the nodes visited by each route and the cost of each
        no_unfulfilled : int
            The number of nodes our reserve trucks must visit

        Notes:
        ------
        Modifies best_routes to include a route for an extra truck which visits
        node whose demand goes unfulfilled when demand is made to vary.
        Modifies routes_input to remove nodes whose demand goes unmet by 'certain' routing
        plan and adds a route to visit these unmet demand nodes.
        This function returns if all clusters have their demand fulfilled.
    '''

    # need to make local copies of inputs so as to not change them in the outer body of any code we use
    # bonus_truck() in
    best_routes = best_routes.copy()
    routes_input = routes_input.copy()
    no_unfulfilled = 0

    # collect those routes whose demand exceeds 20
    unfulfillable_routes = []
    for path in route_paths:
        path_demand = 0
        for store in path:
            path_demand += Demand[store]

        if (path_demand>20):
            unfulfillable_routes.append(path)

    # NB IF ALL ROUTES ARE FULFILLED - DO NOT NEED THIS FUNCTION - CAN RETURN
    if (len(unfulfillable_routes)==0):
        # NB even if all routes fulfilled 
        # need to calculate the new times from uncertain traffic etc.

        # get the names of nodes in the routes:
        route_paths = get_path(best_routes, routes_input)
        i = 0 # index into list of LpVariables storing the best routes
        for route in route_paths:
            # get the supply origin of these changes routes
            row_no = int(best_routes[i].name[6:])
            row_for_route = routes_input[row_no,:]
            # calculate new time and re-write corresp  time costs
            new_time_cost = route_time(route, Supply=row_for_route[-1], Demands=Demand, Times=Times)
            # as always, second-to-last row contains time cost
            routes_input[row_no, -2] = new_time_cost
            # best_routes and routes_paths should be of the same length
            i += 1

        return best_routes, routes_input, no_unfulfilled

    # key for taking second element for store name-demand pair
    def takeSecond(elem):
        return elem[1]

    # find the nodes within each route whose demand is less than 20 and 
    # is the smallest in the route
    # ASSUMPTION: NB we assume there can be  multiple nodes in a cluster whose demand goes unfulfilled.
    min_demand_nodes = []
    for path in unfulfillable_routes:
        path_demands = []
        for store in path:
            path_demands.append([store,Demand[store]])
        
        # sort is ascending by default
        path_demands.sort(key=takeSecond)
        #min_d_node=path_demands[0]


        i = 0
        path_dems_array = np.array(path_demands) # convert for array slicing
        demands = np.array(path_dems_array[:,1]).astype(np.float)
        try:
            while (demands[i] < (np.sum(demands)-20)):
            #min_demand_nodes.append(path_demands[i])
                i += 1
            
            min_demand_nodes.append(path_demands[i])
        except IndexError:
            # for the case when there is no one node with demand greater than the shortfall
            min_demand_nodes.append(path_demands[i-1])
            min_demand_nodes.append(path_demands[0])
            # the above appending assumes that the shortfall is only slightly larger than the 
            # largest demand node e.g: shortfall = 12, largest demand = 11, smallest = 1

        
        

    # get list of stores
    # Load in our string names
    data = np.genfromtxt('demandDataUpdated.csv', skip_header=1, delimiter=',', dtype=None)

    # Extract the list of names of stores, in the correct order - as dictated by demand 
    # dictionary
    names = []
    for line in data:
        line = list(line)
        names.append(line[0].decode('utf-8'))

    # make dictionary to store node names and corresponding columns
    node_cols = {}
    # eliminate these min demand nodes from their original paths
    #min_d_node_cols = [] # store corresp columns in routes input of these min dem nodes 
    for node in min_demand_nodes:
        node_col_no = 0
        for name in names:
            if(node[0]==name):
                # can set all of these to zero since final solution only visits these once
                routes_input[:,node_col_no] = 0
                node_cols[name] = node_col_no    
                #min_d_node_cols.append(node_col_no)
            node_col_no += 1
    
    # TO-DO:
    # ASSUMPTION: find a route to be visited by ONE truck per unfulfilled node
    no_unfulfilled = len(min_demand_nodes)
    # change list of nodes to allow nested array ops
    min_demand_nodes = np.array(min_demand_nodes)

    # send one truck to each node seperately
    for node in min_demand_nodes:

        # work out which distribution center is closer
        if (North_Closed==True):
            supply = False # must originate from south
        else:
            supply = find_closest_distr(node[0], regions)

        # new route to visit - extra two entries for supply and cost
        bonus_route = np.zeros(len(names)+2)
        node_col = node_cols[node[0]] # get the column in route_inputs corresp to this node
        bonus_route[node_col] = 1  # we must visit it
        bonus_route[-1] = supply # set the origin point for this node
        
        routes_input = np.append(routes_input,[bonus_route],axis=0)
        # since best_routes is list of LpVars need to enter 5000+nth route as this:
        bonus_route_no = "{:d}".format(len(routes_input)-1)
        bonus_route_var = LpVariable("Route_"+bonus_route_no, 0, None, LpInteger)
        best_routes.append(bonus_route_var)

    '''
    # code for ONE TRUCK
    # new route to visit - extra two entries for supply and cost
    bonus_route = np.zeros(len(names)+2)

    # assign cost and origin point
    if (North_Closed==True):
        # if north closed, no choice about pt of origin
        bonus_route[-2] = route_time(min_demand_nodes[:,0], Supply=False, Demands=Demand, Times=Times)
    else:
        # check effect of distribution on cost
        bonus_cost_sth = route_time(min_demand_nodes[:,0], Supply=False, Demands=Demand, Times=Times)
        bonus_cost_nth = route_time(min_demand_nodes[:,0], Supply=True, Demands=Demand, Times=Times)
        
        if(bonus_cost_nth < bonus_cost_sth):
            bonus_route[-2] = bonus_cost_nth
            bonus_route[-1] = 1
        else:
            bonus_route[-2] = bonus_cost_sth
            bonus_route[-1] = 0

    for node_col in min_d_node_cols:
        order = 1 # order to visit nodes in 
        for i in range(len(bonus_route)):
            if(i==node_col):
                bonus_route[i] = order
                order+=1
            
    routes_input = np.append(routes_input,[bonus_route],axis=0)
    # since best_routes is list of LpVars need to enter 5001st route as this:
    bonus_route_no = "{:d}".format(len(routes_input)-1)
    bonus_route_var = LpVariable("Route_"+bonus_route_no, 0, None, LpInteger)
    best_routes.append(bonus_route_var)
    '''

    # update all the costs in routes_input for routes in best_route

    # get the names of nodes in the routes:
    route_paths = get_path(best_routes, routes_input)
    i = 0 # index into list of LpVariables storing the best routes
    for route in route_paths:
        # get the supply origin of these changes routes
        row_no = int(best_routes[i].name[6:])
        row_for_route = routes_input[row_no,:]
        # calculate new time and re-write corresp  time costs
        new_time_cost = route_time(route, Supply=row_for_route[-1], Demands=Demand, Times=Times)
        # as always, second-to-last row contains time cost
        routes_input[row_no, -2] = new_time_cost
        # best_routes and routes_paths should be of the same length
        i += 1
    
    return best_routes, routes_input, no_unfulfilled


def find_closest_distr(store, regions):
    ''' Finds the closest distribution given a store and the list of regions

        Parameters:
        -----------
        store : str
            Name of the store
        regions : list
            Nested list of all stores grouped into 5 regions

        Returns:
        --------
        Supply : bool
            If true, North closest. If false, South closest
    '''
    # find the region no. of the store
    def get_region_no():
        region_counter = 0
        for cluster in regions:
            for name in cluster:
                if(name==store):
                    return region_counter # stop counting regions - have found which region store is in

            region_counter += 1
        
    
    region_counter = get_region_no()
    if ((region_counter==0) or (region_counter==1) or (region_counter==4)):
        # regions 0, 1, 4 all have North Supply origins
        return True
    else:
        return False


def calculate_cost(best_routes, routes_input):
   # if trucks are less than 25 then add extra truck at $175 an hour
   # if > 4 hours then add $250 per hour charge
   # find costs of best_routes
   # else need to wet-lease
    new_cost = 0
   # check number of routes are less than 50 (each truck has up to 2 shifts)
    if len(best_routes) < 50:
        for i in best_routes:
            row_no = int(i.name[6:]) # get route number
            time = routes_input[row_no,-2]
            # check if route is over 4 hours
            if time > 14400:
                new_cost += 14400*(175/3600) + (time-14400)*(250/3600)
            else:
                new_cost += time*(175/3600) # find route in routes_input and sum cost
    else:
        for i in range(50): # cost for first 50 routes
            row_no = int(best_routes[i].name[6:]) # get route number
            time = routes_input[row_no,-2]
            # check if route is over 4 hours
            if time > 14400:
                new_cost += 14400*(175/3600) + (time-14400)*(250/3600)
            else:
                new_cost += time*(175/3600) # find route in routes_input and sum cost
        for i in range(50,len(best_routes)): # cost for routes after 50
            row_no = int(best_routes[i].name[6:]) # get route number
            time = routes_input[row_no,-2]
            new_cost += (time/14400)*1500
    return new_cost


if __name__ == "__main__":
    regions = region_divide()
    routes_input = all_routes(regions, North_Closed=False, Saturday=False)
    best_routes, cost=solve_lp(routes_input, Saturday=False)
    route_paths = get_path(best_routes, routes_input)

    regions = region_divide()
    routes_input2 = all_routes(regions, North_Closed=True, Saturday=False)
    best_routes2, cost2=solve_lp(routes_input, Saturday=False)
    route_paths2 = get_path(best_routes, routes_input)


    # Simulation code
    costs = []
    costs_sat = []

    for i in range(10000):
        print("Simulation", i)
        wkdayTimes, saturdayTimes = traffic()
        d = demand()

        best_routesi, routes_inputi, unfulfilled = bonus_truck(route_paths, best_routes, routes_input, d, wkdayTimes, regions)
        best_routesj, routes_inputj, unfulfilled = bonus_truck(route_paths2, best_routes2, routes_input2, d, wkdayTimes, regions, North_Closed = True)
        costs.append(calculate_cost(best_routesj, routes_inputj) - calculate_cost(best_routesi, routes_inputi))

    regions = region_divide()
    routes_input = all_routes(regions, North_Closed=False, Saturday=True)
    best_routes, cost=solve_lp(routes_input, Saturday=True)
    route_paths = get_path(best_routes, routes_input)

    regions = region_divide()
    routes_input2 = all_routes(regions, North_Closed=True, Saturday=True)
    best_routes2, cost2=solve_lp(routes_input, Saturday=True)
    route_paths2 = get_path(best_routes, routes_input)

    for i in range(10000):
        print("Simulation", i)
        wkdayTimes, saturdayTimes = traffic()
        d = demand(Saturday = True)

        best_routesi, routes_inputi, unfulfilled = bonus_truck(route_paths, best_routes, routes_input, d, saturdayTimes, regions)
        best_routesj, routes_inputj, unfulfilled = bonus_truck(route_paths2, best_routes2, routes_input2, d, saturdayTimes, regions, North_Closed = True)
        costs_sat.append(calculate_cost(best_routesj, routes_inputj) - calculate_cost(best_routesi, routes_inputi))

    savings = [20 * costs[i] + 4 * costs_sat[i] for i in range(10000)]
    savings.sort()

    plt.hist(savings, 500)

    print(savings[500], "to", savings[-500])

    plt.show()

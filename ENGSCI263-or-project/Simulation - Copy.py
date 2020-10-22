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

if __name__ == "__main__":
    # Simulation code
    costs = []

    for i in range(1000):
        print("Simulation", i)
        wkdayTimes, saturdayTimes = traffic()
        d = demand()

        regions = region_divide()
        routes_input = all_routes(regions, d, wkdayTimes, North_Closed=False, Saturday=False)
        best_routes, cost=solve_lp(routes_input, Saturday=False)
        route_paths = get_path(best_routes, routes_input)

        costs.append(cost)

    plt.hist(costs, 50)
    costs.sort()

    print(costs[5], "to", costs[-5])

    plt.show()

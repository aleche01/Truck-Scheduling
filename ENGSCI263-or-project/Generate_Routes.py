# This script contains the functions required to generate viable routes for buses in
# the OR project

import numpy as np
import random

def load_data(Saturday = False):
    ''' 
    Loads the demand and store location data from the .csv files into respective lists.

    Returns:
    ----------
    Demand : dictionary
        A dictionary containing the demand averaged over the period at which the data was provided,
        for each store

    Longitude : dictionary
        A dictionary containing the longitude of a given store

    Latitude : dictionary
        A dictionary containing the longitude of a given store

    Location : dictionary
        A dictionary containing the district of a given store, as a string

    Distances : 2D dictionary
        A dictionary containing dictionaries of the distance between two stores

    Times : 2D dictionary
        A dictionary containing dictionaries of the times between two stores, as a truck
        would take

    Notes:
    ----------
    This function is hard coded to load in the data from:
        WarehouseDistances.csv, WarehouseDurations.csv, WarehouseLocations.csv, 
        demandDataUpdated.csv
    '''
    # Read in the demand data, and take the mean demands through time
    data = np.genfromtxt('demandDataUpdated.csv', skip_header=1, delimiter=',', dtype=None)

    names = []
    mean_demand = []
    for line in data:
        line = list(line)
        names.append(line[0].decode('utf-8'))
        #mean_demand.append(np.mean(line[1:]))

        if Saturday:
            saturday_demand = []
            [saturday_demand.append(line[i]) for i in np.arange(1, len(line[1:])) if (i%7 == 6)]
            mean_demand.append(np.ceil(np.mean(saturday_demand)))

        else:
            weekday_demand = []
            [weekday_demand.append(line[i]) for i in np.arange(1, len(line[1:])) if not((i%7 == 6)|(i%7==0))]
            mean_demand.append(np.ceil(np.mean(weekday_demand)))


    # Convert into a dictionary form
    Demand = {names[i]: mean_demand[i] for i in range(len(names))}

    # Read in the demand data, and take the mean demands through time
    data = np.genfromtxt('WarehouseLocations.csv', skip_header=1, delimiter=',', dtype=None)

    names = []
    longitude = []
    latitude = []
    location = []

    for line in data:
        line = list(line)
        names.append(line[2].decode('utf-8'))
        longitude.append(line[3])
        latitude.append(line[4])
        location.append(line[1].decode('utf-8'))
        
    # Convert into dictionary form
    Longitude = {names[i]: longitude[i] for i in range(len(names))}
    Latitude = {names[i]: latitude[i] for i in range(len(names))}
    Location = {names[i]: location[i] for i in range(len(names))}

    # Read in the distances and times between each store into a double dictionary
    time_data = np.genfromtxt('WarehouseDurations.csv', skip_header=1, delimiter=',', dtype=None)
    distance_data = np.genfromtxt('WarehouseDistances.csv', skip_header=1, delimiter=',', dtype=None)

    lookup_times = []
    lookup_distances = []

    for line in time_data:
        line = list(line)
        times = line[1:]
        lookup_times.append({names[i]: times[i] for i in range(len(names))})

    for line in distance_data:
        line = list(line)
        distances = line[1:]
        lookup_distances.append({names[i]: distances[i] for i in range(len(names))})

    # Convert into dictionary form
    Times = {names[i]: lookup_times[i] for i in range(len(names))}
    Distances = {names[i]: lookup_distances[i] for i in range(len(names))}

    return Demand, Longitude, Latitude, Location, Distances, Times


def region_divide():
    ''' 
    Divides the collection of Auckland stores into geographical regions based on longitude and latitude

    Returns:
    ----------
    Regions: 2d-list
        A list of lists containing the strings of stores located in each region as specified by this function

    Notes:
    ----------
    This function has hard coded regions.
    '''
    # Load in all data
    _, Longitude, Latitude, _, _, _ = load_data()

    # Initialise groups
    group1 = []
    group2 = []
    group3 = []
    group4 = []
    group5 = []

    # Cycle through all stores
    for store in Longitude:
        
        # Check for distribution centres instead of stores
        if store == 'Distribution North' or store == 'Distribution South':
            continue

        # If statements to categorise the stores into locations
        elif Latitude[store] > -36.83 and Longitude[store] > 174.67:
            group1.append(store)

        elif Longitude[store] < 174.65:
            group2.append(store)

        elif Latitude[store] < -36.92:
            group3.append(store)

        elif Latitude[store] < -36.88 and Longitude[store] > 174.75:
            group4.append(store)

        else:
            group5.append(store)
    
    # Return these groups in a list
    return [group1, group2, group3, group4, group5]

def route_time(Stores, Supply, Demands, Times, demand = False):
    ''' 
    Given a list of strings representing nodes of a particular route, along with the associated
    supply, and returns the time taken for a truck to traverse a route with these nodes, starting
    and ending at the supply

    Parameters:
    ----------
    Stores: list
        A list of strings containing the names of the stores to visit
    
    Supply: Boolean
        TRUE is the supply is North, FALSE otherwise

    Returns:
    ----------
    time: float
        The time taken (in hours) to traverse the speicifed route by truck
    '''

    # Select appropriate supply
    if Supply:
        supply = "Distribution North"
    else:
        supply = "Distribution South"

    # Initialise the current position as the supply, and time taken as zero
    current = supply
    time = 0.0
    Demand = 0.0

    # Cycle through all listed stores, 
    for store in Stores:
        if demand:
            # Add the time between the current position and the store
             Demand += Demands[store]

        else:
            # Add the time between the current position and the store
            time += Times[current][store]
            time += Demands[store] * 600

        # Update current position
        current = store

    # Add the time it takes to get home
    time += Times[current][supply]
    if demand:
        return Demand
    else:    
        return time

def all_routes(regions, North_Closed = False, Saturday = False):
    '''
    Given a subset of nodes, generates all possible routes through these nodes (demand greater than 15, less than 20, time less than 4 hrs).

    Parameters:
    -------------  
    regions: 2-D list
        A list of lists containing sets of nodes.

    Returns:
    --------------
    all_routes: 2D array
        2D array containing routes and their costs along with classifying them as either north or south.

    '''
    # Load in demands and times
    Demand, _, _, _, _, Times = load_data(Saturday=Saturday)

    # check for no demand stores (ie Noel Leeming on Sat)
    for store in Demand:
        if Demand[store] == 0:
            # can't use .remove directly on nested list
            for i in range(len(regions)):
                if store in regions[i]:
                    regions[i].remove(store)

    print(regions)

    # set up the all_routes matrix
    all_routes = []
    times = []
    random.seed(1896)

    # get all permutations of subset with length 1, 2, 3, nodes etc
    for i in range(len(regions)):

        for j in range (200):
            route = []
            nodes = regions[i].copy()

            while (route_time(route, (i==0 or i==1 or i==4) and (not(North_Closed)), Demand, Times, demand=True) < 18) and (route_time(route, (i==0 or i==1 or i==4) and (not(North_Closed)), Demand, Times)<21600) and nodes != []:
                node = random.choice(nodes)
                route.append(node)
                nodes.remove(node)

            if not ((route_time(route, (i==0 or i==1 or i==4) and (not(North_Closed)), Demand, Times, demand=True) < 18) and (route_time(route, (i==0 or i==1 or i==4) and (not(North_Closed)), Demand, Times)<21600)):
                route.remove(node)

            # Append the time
            times.append(route_time(route, (i==0 or i==1 or i==4) and (not(North_Closed)), Demand, Times))

            all_routes.append(route)

    # Format our data in the correct way
    Grid = np.zeros((1000, 42))

    # Load in our string names
    data = np.genfromtxt('demandDataUpdated.csv', skip_header=1, delimiter=',', dtype=None)

    # Extract the list of names of stores, in the correct order - as dictated by demand 
    # dictionary
    names = []
    for line in data:
        line = list(line)
        names.append(line[0].decode('utf-8'))

    # Cycle through all routes, and format into a grid for LP solver
    for i in range(len(all_routes)):

        # Initialise count
        count = 1

        # Cycle through route
        for j in all_routes[i]:
            # Switch nodes in route from 0 to their position in the overall grid
            index = names.index(j)
            Grid[i][index] = count
            # Update count
            count += 1

        # If route comes from North Supply, change 41st column to 1
        if not (North_Closed):
            if i < 400 or i > 799:
                Grid[i][41] = 1

        # 40th column is the time of the route
        Grid[i][40] = times[i]

    return Grid
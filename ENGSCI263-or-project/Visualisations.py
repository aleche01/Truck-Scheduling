import folium
import numpy as np
import openrouteservice as ors
import pandas as pd

from Generate_Routes import *
from Solve_LP import *
from Simulation import *

#PLOTTING INITIAL MAP
ORSkey = '5b3ce3597851110001cf62489af048ac83e54951bd0192b056e774a0'
locations = pd.read_csv("WarehouseLocations.csv")

coords_unindexed = locations[['Long', 'Lat']]
coords_unindexed = coords_unindexed.to_numpy().tolist()

m = folium.Map(location = list(reversed(coords_unindexed[2])), zoom_start = 10)

folium.Marker(list(reversed(coords_unindexed[0])), popup = locations.Store[0], icon = folium.Icon(color ='black')).add_to(m)

for i in range(1, len(coords_unindexed)):
    if locations.Type[i] == "The Warehouse":
        iconCol = "red"
    elif locations.Type[i] == "Noel Leeming":
        iconCol = "orange"
    elif locations.Type[i] == "Distribution":
        iconCol = "black"
    folium.Marker(list(reversed(coords_unindexed[i])), popup = locations.Store[i], icon = folium.Icon(color = iconCol)).add_to(m)

m.save("InitialMap.html")

client = ors.Client(key=ORSkey)

#############################
#ADDING ROUTES
#regions = region_divide()
#routes_input = all_routes(regions, North_Closed=False, Saturday=False)
#best_routes, cost = solve_lp(routes_input, Saturday=False)
wkdayTimes, saturdayTimes = traffic()
d = demand()
regions = region_divide()
routes_input_I = all_routes(regions, North_Closed=False, Saturday=False)
best_routes_I, cost=solve_lp(routes_input_I, Saturday=False)
route_paths = get_path(best_routes_I, routes_input_I)
best_routes, routes_input, unfulfilled = bonus_truck(route_paths, best_routes_I, routes_input_I, d, wkdayTimes, regions, North_Closed=False)

real_route_paths = get_path(best_routes, routes_input)

#load data
Demand, Longitude, Latitude, Location, Distances, Times = load_data(Saturday = False)

#indexing of data
Ordered_Longitude = []
Ordered_Latitude = []
for key in Demand.keys():
    for key2 in Longitude.keys():
        if key == key2:
            Ordered_Longitude.append(Longitude[key2])

for key in Demand.keys():
    for key2 in Latitude.keys():
        if key == key2:
            Ordered_Latitude.append(Latitude[key2])

#store coordinates
coords = []
for i in range(len(Ordered_Longitude)):
    coords.append([Ordered_Longitude[i], Ordered_Latitude[i]])

#color each route differently
w = 0
#colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'black', 'darkred', 'white', 'gold', 'brown', 'darkgreen', 'magenta', 'silver', 'teal']

#colors = ['black']*len(best_routes)
colors = ['black']*(len(best_routes)-unfulfilled)
colors.extend(['red']*unfulfilled)

for routes in best_routes:
    print(routes)
    coordinates = []
    intRouteNumber = int(routes.name.replace("Route_", ""))
    route_info = routes_input[intRouteNumber]
    
    #assuming 0 is south and 1 is north
    if route_info[41] == 1:
        #starting point
        coordinates.append(coords_unindexed[1]) #north supply
    if route_info[41] == 0:
        coordinates.append(coords_unindexed[0]) #south supply

    lengthRoute = 0
    # -2 because supply and cost variables not needed.
    # get number of Nodes visited
    for i in range(len(route_info)-2):
        if route_info[i] != 0:
            lengthRoute = lengthRoute + 1
   
    #h = 1 #destination number
    route_nodes = route_info[:-2]
    # get the ordering of the nodes
    h = route_nodes[np.nonzero(route_nodes)]
    #loops through first, second, third... destinations
    for order in h:
        for j in range(len(route_info)-2):
            if route_info[j] == order:
                coordinates.append(coords[j])
        #h = h + 1

    #ending point
    if route_info[41] == 1:
        coordinates.append(coords_unindexed[1]) #north supply
    if route_info[41] == 0:
        coordinates.append(coords_unindexed[0]) #south supply
    
    route = client.directions(coordinates = coordinates, profile = 'driving-hgv', format = 'geojson', validate = False)

    folium.PolyLine(locations = [list(reversed(coord)) for coord in route['features'][0]['geometry']['coordinates']], color = colors[w]).add_to(m)
    m.save("testRoute1.html")

    w = w+1


library(tidyverse)
library(leaflet)
locations = read_csv("WarehouseLocations.csv")

map = leaflet()
map = addTiles(map)

locations$loc[locations$Long > 174.6] <- "group5"
locations$loc[locations$Lat > -36.83 & locations$Long > 174.67] <- "group1"
locations$loc[locations$Long < 174.65] <- "group2"
locations$loc[locations$Lat < -36.88 & locations$Long > 174.75] <- "group4"
locations$loc[locations$Lat < -36.92] <- "group3"
locations$loc[locations$Type == "Distribution"] <- "distribution"

ColorLoc = colorFactor(c("darkgreen", "orange", "darkred", "blue", "purple", "black"), domain = c("distribution", "group1", "group2", "group3", "group4", "group5"))
d =leaflet(locations)%>%addTiles()%>%addCircleMarkers(color=~ColorLoc(loc), stroke=TRUE,radius=10)
d %>% addLegend("bottomright", pal = ColorLoc, values =~loc, title = "Grouped Areas")

install.packages("tidyverse")
library(tidyverse)

demand = read_csv("demandDataUpdated.csv")


demand_wkday <- demand[c(1, 2:6, 9:13, 16:20, 23:27)]
demand_sat <- demand[c(1,7,14,21,28)]


demand_wkday_gather = gather(demand_wkday, key = Date, value = demand_wkday, contains("2020"))
demand_wkday_name = demand_wkday_gather %>% group_by(Name) %>% summarise(AvgDailyDemand = ceiling((sum(demand_wkday)/20)))

ggplot(data= demand_wkday_name) + geom_col(mapping=aes(x=AvgDailyDemand, y=Name))+ labs(title = "Weekday mean demand at each store over 4 weeks", y="Store name", x= "Average demand [pallets]")


demand_sat_gather = gather(demand_sat, key = Date, value = demand_sat, contains("2020"))
demand_sat_name = demand_sat_gather %>% group_by(Name) %>% summarise(AvgDailyDemand = ceiling((sum(demand_sat)/4)))

ggplot(data= demand_sat_name) + geom_col(mapping=aes(x=AvgDailyDemand, y=Name))+ labs(title = "Saturday mean demand at each store over 4 weeks", y="Store name", x= "Average demand [pallets]")

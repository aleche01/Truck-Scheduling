library(tidyverse)
library(ggplot2)
library(lubridate)
library(boot)

demand = read_csv("demandDataUpdated.csv")

demand$Store = c(rep("Noel Leeming",20),rep("Warehouse",20))

demand = gather(demand, key = Date, value = Pallets, -Name, -Store)

demand$Date = parse_date_time(demand$Date,"dmy")

demand$Store = as.factor(demand$Store)

demand$Day = wday(demand$Date, label = TRUE)

demand = filter(demand, (Store == "Warehouse" & Day != "Sat" & Day != "Sun"))

mean_pallet <- function(data, indices){
  dt = data[indices,]
  c(
    mean(dt$Pallets),
    sd(dt$Pallets)
  )
}

bootstrap = boot(demand, mean_pallet, R=1000)

bootstrap = tibble(mean = bootstrap$t[,1], std = bootstrap$t[,2])

ggplot(bootstrap) + geom_bar(aes(x = mean))

ggplot(bootstrap) + geom_bar(aes(x=std))
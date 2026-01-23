library(tidyverse)

read_csv()

read_csv("data/stimuli/v2/R2 Op. 19, No. 5 condition 1.csv") %>%
  mutate(piece = "Op. 19, No. 5", condition = paste(piece, "condition 1"))

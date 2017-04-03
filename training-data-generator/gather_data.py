import subprocess
import numpy as np
import os

start = 0
out_file = open("score-distribution.csv","w+")
output = ''

while os.path.exists("training-data/set-"+str(start)+".csv") == True:
  sample_file = open("training-data/set-"+str(start)+".csv", "r")
  lines = sample_file.readlines()
  sample_file.close()
  for line in lines:
    output += line  
  start = start + 1

out_file.write(output)
out_file.close()

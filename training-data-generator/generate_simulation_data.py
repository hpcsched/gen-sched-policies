#This program is free software; you can redistribute it and/or modify it

from __future__ import print_function
import numpy as np
import re
import random
import subprocess
import sys
import os.path
#import cStringIO

filename = "lublin_256.swf"

model_num_nodes = []
model_run_times = []
model_submit_times = []
num_tasks_queue = 32
num_tasks_state = 16
earliest_submit = 0
tasks_state_nodes = []
tasks_state_runtimes = []
tasks_state_submit = []
tasks_queue_nodes = []
tasks_queue_runtimes = []
tasks_queue_submit = []
num_trials = 5000

for line in file(filename):
  row = re.split(" +", line.lstrip(" "))
  if row[0] == ';':
    continue
  #print("%f %d" % (float(row[4]), int(row[5])))  
  if int(row[4]) > 0 and int(row[4]) <= 256 and int(row[3]) > 0:
    model_run_times.append(int(row[3]))
    model_num_nodes.append(int(row[4]))
    model_submit_times.append(int(row[1])) 

#random.seed(None)

start = 0
while os.path.exists("task-sets/set-"+str(start)+".csv") == True:
  start = start+1

#if start != 0: 
#  start = start-1

for i in xrange(start,2): #maximum number os tuples (S,Q) to be simulated 
  task_file = open("task-sets/set-"+str(i)+".csv", "w+")
  tasks_state_nodes = []
  tasks_state_runtimes = []
  tasks_state_submit = []
  choose = random.randint(0,len(model_run_times)-1 - (num_tasks_queue+num_tasks_state))
  earliest_submit = model_submit_times[choose]
  for j in xrange(0,16):
    tasks_state_nodes.append(model_num_nodes[choose+j])
    tasks_state_runtimes.append(model_run_times[choose+j])
    tasks_state_submit.append(model_submit_times[choose+j] - earliest_submit)
    task_file.write(str(tasks_state_runtimes[j])+","+str(tasks_state_nodes[j])+","+str(tasks_state_submit[j])+"\n")
  tasks_queue_nodes = []
  tasks_queue_runtimes = []
  tasks_queue_submit = []
  for j in xrange(0,32):
    #choose = random.randint(0,len(model_run_times)-1)
    tasks_queue_nodes.append(model_num_nodes[num_tasks_state+choose+j])
    tasks_queue_runtimes.append(model_run_times[num_tasks_state+choose+j])
    tasks_queue_submit.append(model_submit_times[num_tasks_state+choose+j] - earliest_submit)
    task_file.write(str(tasks_queue_runtimes[j])+","+str(tasks_queue_nodes[j])+","+str(tasks_queue_submit[j])+"\n")
  task_file.close()
 
  
  
  perm_indices = np.empty(shape=(num_trials, num_tasks_queue), dtype=int)
  for j in xrange(0,num_trials):
    perm_indices[j] = np.arange(32)

  #print(perm_indices)

  #permutation_file = open("perm-indices/set"+str(i)+".csv", "w+")
  
  subprocess.call(['cp task-sets/set-'+str(i)+'.csv' ' current-simulation.csv'], shell=True)  
  subprocess.call(['./trials_simulator simple_cluster.xml deployment_cluster.xml -state > states/set'+str(i)+".csv"], shell=True)

  if(os.path.exists("result-temp.dat") == True):
    subprocess.call(['rm result-temp.dat'], shell=True)
  
  if(os.path.exists("training-data/set-"+str(i)+".csv") == True):
    subprocess.call(['rm training-data/set-'+str(i)+'.csv'], shell=True)  

  shufle_tasks_queue_runtimes = np.copy(tasks_queue_runtimes)
  shuffle_tasks_queue_nodes = np.copy(tasks_queue_nodes)
  shuffle_tasks_queue_submit = np.copy(tasks_queue_submit)

  for j in xrange(0,num_trials): #10000
    #iteration_file = open("iterations/set"+str(i)+"-it"+str(j)+".csv", "w+")
    iteration_file = open("current-simulation.csv", "w+")
    #iteration_file = cStringIO.StringIO()
    #random shuffle between the tasks in the queue
    for k in xrange(0,32):
      choose = random.randint(0,31)
      buffer_runtimes = shufle_tasks_queue_runtimes[choose]
      buffer_nodes = shuffle_tasks_queue_nodes[choose] 
      buffer_submit = shuffle_tasks_queue_submit[choose]     
      shufle_tasks_queue_runtimes[choose] = shufle_tasks_queue_runtimes[k]
      shuffle_tasks_queue_nodes[choose] = shuffle_tasks_queue_nodes[k]
      shuffle_tasks_queue_submit[choose] = shuffle_tasks_queue_submit[k]
      shufle_tasks_queue_runtimes[k] = buffer_runtimes
      shuffle_tasks_queue_nodes[k] = buffer_nodes 
      shuffle_tasks_queue_submit[k] = buffer_submit      
      buffer_index = perm_indices[j,choose]
      perm_indices[j,choose] = perm_indices[j,k]
      perm_indices[j,k] = buffer_index;
    for k in xrange(0,16):      
      iteration_file.write(str(tasks_state_runtimes[k])+","+str(tasks_state_nodes[k])+","+str(tasks_state_submit[k])+"\n")
    for k in xrange(0,32):   
      iteration_file.write(str(tasks_queue_runtimes[perm_indices[j,k]])+","+str(tasks_queue_nodes[perm_indices[j,k]])+","+str(tasks_queue_submit[perm_indices[j,k]])+"\n")
      #if j == 0:
      #  permutation_file.write(str(perm_indices[j]))
      #elif 0 < j and j < 31:
      #  permutation_file.write(","+str(perm_indices[j]))
      #else:
      #  permutation_file.write(","+str(perm_indices[j])+"\n")
    iteration_file.close()
    
    subprocess.call(['./trials_simulator simple_cluster.xml deployment_cluster.xml >> result-temp.dat'], shell=True)
  #permutation_file.close()

  output = "" 
  exp_sum_slowdowns = 0.0
  distribution = np.zeros(num_tasks_queue)
  exp_first_choice = np.zeros((num_trials), dtype=np.int32)
  exp_slowdowns = np.zeros((num_trials))
  state = ""

  task_sets_prefix = "task-sets/set-"  
  results_prefix = "results/set"
  states_prefix = "states/set"

  for trialID in xrange(0,num_trials):
    exp_first_choice[trialID] = perm_indices[trialID,0] #asserted
    #print(exp_first_choice[trialID])
    #print(perm_indices[trialID,:])

  trialID = 0
  result_file = open("result-temp.dat", "r")
  lines = result_file.readlines()
  if len(lines) != num_trials:
    result_file.close()
    i = i - 1
    continue
  for line in lines:
    #print("%f %d" % (float(row[4]), int(row[5])))
    exp_slowdowns[trialID] = float(line)
    exp_sum_slowdowns += float(line)    
    trialID = trialID + 1
  result_file.close() 

  #print("%.2f %.2f [%d %d]" % (np.mean(slow_zero), np.mean(slow_one), len(slow_zero), len(slow_one)))
    
  for line in file(states_prefix + str(i) + ".csv"):
    state = str(line)

  for trialID in xrange(0, len(exp_slowdowns)):
    distribution[exp_first_choice[trialID]] += exp_slowdowns[trialID]

  #output += state.rstrip('\n') + ","


  for k in xrange(0, len(distribution)):
    distribution[k] = distribution[k] / exp_sum_slowdowns
    #debug += distribution[j]
  
  for k in xrange(0,num_tasks_queue):
    #print("%d %d" % (model_run_times[j], model_num_nodes[j]))
    output += str(int(tasks_queue_runtimes[k])) + "," + str(int(tasks_queue_nodes[k])) + "," + str(int(tasks_queue_submit[k])) + ","
    output += str(distribution[k]) + "\n"
   

  out_file = open("training-data/set-"+str(i)+".csv","w+")
  out_file.write(output)
  out_file.close() 
  #print(output)



#print("%d" % random.randint(2,8))
  

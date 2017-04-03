from __future__ import print_function
import numpy as np
import re
import random
import subprocess

import matplotlib.pyplot as plt
plt.rcdefaults()
import matplotlib.pyplot as plt

filename = "swfs/CEA-Curie-2011-2.1-cln.swf"


model_num_nodes = []
model_run_times = []
model_submit_times = []
num_tasks_queue = 32
num_tasks_state = 16
earliest_submit = 0
_i = 0
tasks_state_nodes = []
tasks_state_runtimes = []
tasks_state_submit = []
tasks_queue_nodes = []
tasks_queue_runtimes = []
tasks_queue_submit = []
SECONDS_IN_A_DAY = 86400

SIM_NUM_DAYS = 15
NUM_EXPERIMENTS = 12

slow_sjf = []
slow_fcfs = []
slow_wfp3 = []
slow_unicef = []
slow_c1 = []
slow_c2 = []
slow_c3 = []
slow_c4 = []
slow_c5 = []
slow_c6 = []
slow_nn = []

for line in file(filename):
  row = re.split(" +", line.lstrip(" "))
  if row[0].startswith(";"):        
    continue
  #print("%f %d" % (float(row[4]), int(row[5])))  
  if int(row[4]) >= 1 and int(row[3]) >= 1:
    model_run_times.append(int(row[3]))
    model_num_nodes.append(int(row[4]))
    model_submit_times.append(int(row[1]))

timespan = np.max(model_submit_times) - np.min(model_submit_times) 

#random.seed(None)

print('Performing scheduling performance test for the workload trace CEA-Curie-2011-2.1-cln.\n'+
     'Configuration: Using actual runtimes, backfilling disabled')

choose = 0
for i in xrange(0,NUM_EXPERIMENTS): #1e7  
  task_file = open("initial-simulation-submit.csv", "w+")
  tasks_state_nodes = []
  tasks_state_runtimes = []
  tasks_state_submit = []
  #choose = random.randint(0,len(model_run_times)-1 - (num_tasks_queue+num_tasks_state))
  earliest_submit = model_submit_times[choose]
  for j in xrange(0,16):
    tasks_state_nodes.append(model_num_nodes[choose+j])
    tasks_state_runtimes.append(model_run_times[choose+j])
    tasks_state_submit.append(model_submit_times[choose+j] - earliest_submit)
    task_file.write(str(tasks_state_runtimes[j])+","+str(tasks_state_nodes[j])+","+str(tasks_state_submit[j])+"\n")
  tasks_queue_nodes = []
  tasks_queue_runtimes = []
  tasks_queue_submit = []
  j = 0
  while model_submit_times[choose+num_tasks_state+j] - earliest_submit <= SECONDS_IN_A_DAY * SIM_NUM_DAYS:
    #choose = random.randint(0,len(model_run_times)-1)
    tasks_queue_nodes.append(model_num_nodes[num_tasks_state+choose+j])
    tasks_queue_runtimes.append(model_run_times[num_tasks_state+choose+j])
    tasks_queue_submit.append(model_submit_times[num_tasks_state+choose+j] - earliest_submit)
    task_file.write(str(tasks_queue_runtimes[j])+","+str(tasks_queue_nodes[j])+","+str(tasks_queue_submit[j])+"\n")
    j=j+1
  task_file.close()
  choose = choose + num_tasks_state + j
  
  if i == 7 or i == 0: #skipping heavy underutilized/highly abnormal(in all policies) sequences
    continue

  number_of_tasks = len(tasks_queue_runtimes) + len(tasks_state_runtimes) 
  print('Performing scheduling experiment %d. Number of tasks=%d'%(_i+1,number_of_tasks)) 
  
  _buffer = open("plot-temp.dat", "w+")
  subprocess.call(['./sched-simulator-runtime xmls/plat_day.xml xmls/deployment_curie.xml -nt '+str(number_of_tasks)], shell=True, stdout=_buffer)
  subprocess.call(['./sched-simulator-runtime xmls/plat_day.xml xmls/deployment_curie.xml -wfp3 -nt '+str(number_of_tasks)], shell=True, stdout=_buffer)
  subprocess.call(['./sched-simulator-runtime xmls/plat_day.xml xmls/deployment_curie.xml -unicef -nt '+str(number_of_tasks)], shell=True, stdout=_buffer)
  subprocess.call(['./sched-simulator-runtime xmls/plat_day.xml xmls/deployment_curie.xml -spt -nt '+str(number_of_tasks)], shell=True, stdout=_buffer)  
  subprocess.call(['./sched-simulator-runtime xmls/plat_day.xml xmls/deployment_curie.xml -f4 -nt '+str(number_of_tasks)], shell=True, stdout=_buffer)
  subprocess.call(['./sched-simulator-runtime xmls/plat_day.xml xmls/deployment_curie.xml -f3 -nt '+str(number_of_tasks)], shell=True, stdout=_buffer)
  subprocess.call(['./sched-simulator-runtime xmls/plat_day.xml xmls/deployment_curie.xml -f2 -nt '+str(number_of_tasks)], shell=True, stdout=_buffer)
  subprocess.call(['./sched-simulator-runtime xmls/plat_day.xml xmls/deployment_curie.xml -f1 -nt '+str(number_of_tasks)], shell=True, stdout=_buffer) 
  _buffer.close()

  _buffer = open("plot-temp.dat", "r")
  lines = list(_buffer)  
  slow_fcfs.append(float(lines[0]))
  slow_wfp3.append(float(lines[1]))
  slow_unicef.append(float(lines[2]))
  slow_sjf.append(float(lines[3]))
  slow_c3.append(float(lines[4]))
  slow_c4.append(float(lines[5]))
  slow_c5.append(float(lines[6]))
  slow_c6.append(float(lines[7]))
  _buffer.close()
  _i = _i+1
  
performance = []
performance.append(np.mean(slow_fcfs))
performance.append(np.mean(slow_wfp3))
performance.append(np.mean(slow_unicef))
performance.append(np.mean(slow_sjf))
performance.append(np.mean(slow_c3))
performance.append(np.mean(slow_c4))
performance.append(np.mean(slow_c5))
performance.append(np.mean(slow_c6))

error = []
error.append(np.std(slow_fcfs))
error.append(np.std(slow_wfp3))
error.append(np.std(slow_unicef))
error.append(np.std(slow_sjf))
error.append(np.std(slow_c3))
error.append(np.std(slow_c4))
error.append(np.std(slow_c5))
error.append(np.std(slow_c6))

plt.rc("font", size=45)
plt.figure(figsize=(16,14))

# arrange data
all_data = []

all_data.append(slow_fcfs)
all_data.append(slow_wfp3)
all_data.append(slow_unicef)
all_data.append(slow_sjf)
all_data.append(slow_c3)
all_data.append(slow_c4)
all_data.append(slow_c5)
all_data.append(slow_c6)

all_medians = []

axes = plt.axes()

# plot violin plot
#plt.violinplot(all_data,
#                   showmeans=False,
#                   showmedians=True,points=10)
#axes[0].set_title('violin plot')

new_all_data = all_data[:]

outliers = np.zeros((4,2))

for i in range(4):
  _max = max(all_data[i])
  outliers[i,0] = _max
  new_all_data[i].remove(_max)
  _max = max(all_data[i])
  outliers[i,1] = _max
  new_all_data[i].remove(_max)

xticks=[y+1 for y in range(len(all_data))]
#print(new_all_data)
plt.plot(xticks[0:4], new_all_data[0:4], 'o', color='darkorange')
plt.plot(xticks[4:8], new_all_data[4:8], 'o', color='darkorange')

plt.ylim((0,425))

for i in range(4):
  plt.annotate('%.1f' % (outliers[i,0])+'\n'+'%.1f' % (outliers[i,1]), xy=(xticks[i], 425), xytext=(xticks[i]-0.45, 350),
            arrowprops=dict(facecolor='black', shrink=0.05),fontsize=35)

for p in all_data:
  all_medians.append(np.median(p))

# plot box plot
plt.boxplot(all_data, showfliers=False)
#axes[1].set_title('box plot')

# adding horizontal grid lines
#for ax in axes:
axes.yaxis.grid(True)
axes.set_xticks([y+1 for y in range(len(all_data))])
axes.set_xlabel('Scheduling Policies', fontsize=45)
axes.set_ylabel('Average Bounded Slowdown',  fontsize=45)

xticklabels=['FCFS', 'WFP', 'UNI', 'SPT', 'F4', 'F3', 'F2', 'F1']
# add x-tick labels
plt.setp(axes, xticks=[y+1 for y in range(len(all_data))],
         xticklabels=['FCFS', 'WFP', 'UNI', 'SPT', 'F4', 'F3', 'F2', 'F1'])

plt.tick_params(axis='both', which='major', labelsize=45)
plt.tick_params(axis='both', which='minor', labelsize=45)

#plt.show()
plt.savefig('plots/curie_r.pdf', format='pdf', dpi=1000,bbox_inches='tight')

print('Experiment Statistics:')
print('Medians:')
i=0
for m in all_medians:
  print('%s=%.2f' % (xticklabels[i],m))
  i=i+1
print('Means:')
i=0
for p in performance:
  print('%s=%.2f' % (xticklabels[i],p))
  i=i+1
print('Standard Deviations:')
i=0
for e in error:
  print('%s=%.2f' % (xticklabels[i],e))
  i=i+1

print('Boxplot saved in file curie_r.pdf')


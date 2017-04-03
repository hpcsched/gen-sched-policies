/* This program is free software; you can redistribute it and/or modify it
 * under the terms of the license (GNU LGPL) which comes with this package. */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include "simgrid/msg.h"            /* Yeah! If you want to use msg, you need to include msg/msg.h */
#include "xbt/sysdep.h"         /* calloc, printf */

/* Create a log channel to have nice outputs. */
#include "xbt/log.h"
#include "xbt/asserts.h"
XBT_LOG_NEW_DEFAULT_CATEGORY(msg_test,
                             "Messages specific for this msg example");

void sortTasksQueue(double* runtimes, int* cores, int* submit, int policy);
const char* getfield(char* line, int num);
void readModelFile(void);
int master(int argc, char *argv[]);
int taskManager(int argc, char *argv[]);
msg_error_t test_all(const char *platform_file,
                     const char *application_file);

#define FINALIZE ((void*)221297)        /* a magic number to tell people to stop working */

#define MAX_TASKS 1024
#define WORKERS_PER_NODE 1
#define MAX_TASK_TYPES 5 
#define TERA 1e12
#define MEGA 1e6
#define TAO 10
#define MODEL_NUM_TASKS 32
#define NUM_TASKS_STATE 16

#define FCFS 0
#define LPT 1
#define WFP3 2
#define UNICEF 3
#define CANDIDATE1 4
#define CANDIDATE2 5

struct task_t{
int numNodes;
double startTime;
double endTime;
double submitTime;
double *task_comp_size;
double *task_comm_size;
msg_host_t* task_workers;
int *task_allocation;
};

//long task_comp_sizes[MAX_TASK_TYPES];
//long task_comm_sizes[MAX_TASK_TYPES];
//int num_tasks[10];
//int tasks_created[10];
//int seed;
int VERBOSE = 0;
int STATE = 0;

double* model_runtimes;
int* model_submit;
int* model_cores;

int* orig_task_positions;

//double** tasks_comp_sizes;
//double** tasks_comm_sizes;
//msg_host_t** tasks_workers;
//int** tasks_allocation;

double* slowdown;

struct task_t* task_queue = NULL;
msg_process_t p_master;

int chosen_policy = FCFS;
int* busy_workers;
int num_managers = MODEL_NUM_TASKS + NUM_TASKS_STATE;

double* sched_task_placement;
//int** sched_task_types;
//int* tasks_per_worker;
int number_of_tasks = MODEL_NUM_TASKS + NUM_TASKS_STATE;
double t0 = 0.0f;

void sortTasksQueue(double* runtimes, int* cores, int* submit, int policy){
  int i, j;
  if(policy == FCFS)
    return;
  if(policy == LPT){
    double r_buffer;
    int c_buffer;
    int s_buffer;
    int p_buffer;	
    for(i = 0; i < MODEL_NUM_TASKS; i++){
      for(j = 0; j < MODEL_NUM_TASKS; j++){
	    if(runtimes[i] > runtimes[j]){
		  r_buffer = runtimes[i];
		  c_buffer = cores[i];
                  s_buffer = submit[i];
                  p_buffer = orig_task_positions[i];
		  runtimes[i] = runtimes[j];
		  cores[i] = cores[j];
                  submit[i] = submit[j];
                  orig_task_positions[i] = orig_task_positions[j];
		  runtimes[j] = r_buffer;
		  cores[j] = c_buffer;
                  submit[j] = s_buffer;
                  orig_task_positions[j] = p_buffer;
		}
	  }     	  
    }
	return;
  }
  double* h_values = (double*) calloc(MODEL_NUM_TASKS, sizeof(double));
  double* r_temp = (double*) calloc(MODEL_NUM_TASKS, sizeof(double));
  int* c_temp = (int*) calloc(MODEL_NUM_TASKS, sizeof(int));
  int* s_temp = (int*) calloc(MODEL_NUM_TASKS, sizeof(int));
  int* p_temp = (int*) calloc(MODEL_NUM_TASKS, sizeof(int));
  int max_arrive = 0;
  for(i = 0; i < MODEL_NUM_TASKS;i++){
    if(submit[i] > max_arrive){
      max_arrive = submit[i];
    }
  }  
  int queue_score = 0;
  for(i = 0; i < MODEL_NUM_TASKS;i++){
    queue_score = max_arrive - submit[i]; //priority score for the arrival time (bigger = came first)
    switch(policy){
      case WFP3:
	    h_values[i] = pow(queue_score/runtimes[i], 3) * cores[i];
            break;
      case UNICEF:
	    h_values[i] = queue_score/(log2((double)cores[i]) * runtimes[i]);
	    break;

      case CANDIDATE1:
          //h_values[i] = log10(runtimes[i]) * sqrt(cores[i]); //candidate 1 (increasing order)
          h_values[i] = (0.0075611 * log10(runtimes[i])) + (0.0113013 * log10(cores[i])); //candidate 1 (increasing order)
          break;
      case CANDIDATE2:
          //h_values[i] = log10(runtimes[i]) * cores[i]; //candidate 2 
          h_values[i] = (0.0066197 * log10(runtimes[i])) + (0.0039650 * sqrt(cores[i])); //candidate 2 
          //h_values[i] = (0.0081926 * log10(runtimes[i])) + (0.0173701* (1.0 / cores[i])); //candidate 2 
          break;
    }	
  }
if(policy == WFP3 || policy == UNICEF){
  double max_val = 0.0;
  int max_index;
  for(i = 0; i < MODEL_NUM_TASKS;i++){
	max_val = 0.0;  
    for(j = 0; j < MODEL_NUM_TASKS; j++){		
	  if(h_values[j] > max_val){
		max_val = h_values[j];
        max_index = j;	
	  }
	}
    r_temp[i] = runtimes[max_index];
    c_temp[i] = cores[max_index];
    s_temp[i] = submit[max_index];
    p_temp[i] = NUM_TASKS_STATE + max_index;
    h_values[max_index] = 0.0;	
  }
}else if(policy == CANDIDATE1 || policy == CANDIDATE2){
  double min_val = 1e20;
  int min_index;
  for(i = 0; i < MODEL_NUM_TASKS;i++){
	min_val = 1e20;  
    for(j = 0; j < MODEL_NUM_TASKS; j++){		
	  if(h_values[j] < min_val){
		min_val = h_values[j];
        min_index = j;	
	  }
	}
    r_temp[i] = runtimes[min_index];
    c_temp[i] = cores[min_index];
    s_temp[i] = submit[min_index];
    p_temp[i] = NUM_TASKS_STATE + min_index;
    h_values[min_index] = 1e20;	
  }
}
  for(i = 0; i < MODEL_NUM_TASKS;i++){
	runtimes[i] = r_temp[i];
	cores[i] = c_temp[i];
        submit[i] = s_temp[i];
        orig_task_positions[i] = p_temp[i];
  }
  free(r_temp);
  free(c_temp);
  free(s_temp);
  free(p_temp);
  free(h_values);
}

const char* getfield(char* line, int num)
{
    const char* tok;
    for (tok = strtok(line, ",");
            tok && *tok;
            tok = strtok(NULL, ",\n"))
    {
        if (!--num)
            return tok;
    }
    return NULL;
}

void readModelFile(void){
    
    model_runtimes = (double*) malloc((MODEL_NUM_TASKS + NUM_TASKS_STATE) * sizeof(double));
    model_submit = (int*) malloc((MODEL_NUM_TASKS + NUM_TASKS_STATE) * sizeof(int));
    model_cores = (int*) malloc((MODEL_NUM_TASKS + NUM_TASKS_STATE) * sizeof(int));
    int task_count=0;    
    
    //FILE* stream = fopen("workload-test.csv.old", "r");
    FILE* stream = fopen("current-simulation.csv", "r");

    char line[1024];
    while (fgets(line, 1024, stream))
    {
        char* tmp = strdup(line);        
        model_runtimes[task_count] = atof(getfield(tmp, 1));
        free(tmp);
        tmp = strdup(line);
        model_cores[task_count] = atoi(getfield(tmp, 2));
        free(tmp);
        tmp = strdup(line);
        model_submit[task_count] = atoi(getfield(tmp, 3));
        free(tmp);
        // NOTE strtok clobbers tmp
        task_count++;      
    }
}

/** Emitter function  */
int master(int argc, char *argv[])
{
  int workers_count = 0;
  msg_host_t *workers = NULL;
  msg_host_t task_manager = NULL;
  msg_task_t *todo = NULL;  
  //double task_comp_size = 0;
  //double task_comm_size = 0;

  int i;

  int res = sscanf(argv[1], "%d", &workers_count);
  xbt_assert(res,"Invalid argument %s\n", argv[1]);
  //res = sscanf(argv[2], "%d", &workers_count);
  //xbt_assert(res, "Invalid argument %s\n", argv[2]);
  //res = sscanf(argv[3], "%lg", &task_comm_size);
  //xbt_assert(res, "Invalid argument %s\n", argv[3]);


  //workers_count = argc - 4;

readModelFile();
orig_task_positions = (int*) malloc(MODEL_NUM_TASKS * sizeof(int));
int c = 0;
for(i = NUM_TASKS_STATE; i < number_of_tasks; i++){
  orig_task_positions[c++] = i;
}
sortTasksQueue(&model_runtimes[NUM_TASKS_STATE], &model_cores[NUM_TASKS_STATE], &model_submit[NUM_TASKS_STATE], chosen_policy);

/*  criacao das matrizes de saída */
//sched_task_placement = (double*) calloc((MAX_TASKS),sizeof(double));
//sched_task_types = (int**) malloc(workers_count*sizeof(int*));

//srand(seed);

p_master = MSG_process_self();
{                             /* Process organisation (workers) */  
    //int i;
    char sprintf_buffer[64];  
    workers = xbt_new0(msg_host_t, workers_count);

    for (i = 0; i < workers_count; i++) {
      sprintf(sprintf_buffer, "node-%d", (i+WORKERS_PER_NODE) / WORKERS_PER_NODE);
      workers[i] = MSG_get_host_by_name(sprintf_buffer);
      xbt_assert(workers[i] != NULL, "Unknown host %s. Stopping Now! ",
                  sprintf_buffer);
    }
}

{                             /* Process organisation (managers) */
    //num_managers = MODEL_NUM_TASKS + NUM_TASKS_STATE;
    task_manager = MSG_get_host_by_name("node-0");
    xbt_assert(task_manager != NULL, "Unknown host %s. Stopping Now! ",
                    "node-0");    
}

if(VERBOSE)
XBT_INFO("Got %d workers and %d tasks to process", workers_count, number_of_tasks);

{                             /*  Task creation */
    int j, k;

    todo = xbt_new0(msg_task_t, number_of_tasks);

    busy_workers = (int*) calloc(workers_count, sizeof(int));
    task_queue = (struct task_t*) malloc(number_of_tasks * sizeof(struct task_t)); 
    //tasks_comp_sizes = (double**) malloc(number_of_tasks * sizeof(double*));
    //tasks_comm_sizes = (double**) malloc(number_of_tasks * sizeof(double*));
    //tasks_allocation = (int**) malloc(number_of_tasks * sizeof(int*));  
    //tasks_workers = xbt_new0(msg_host_t**, number_of_tasks);
    
    for (i = 0; i < number_of_tasks; i++) {
      int available_nodes;  
      do{
        while(MSG_get_clock() < model_submit[i]){//task has not arrived yet 
          MSG_process_sleep(model_submit[i] - MSG_get_clock());
        }
        available_nodes = 0;
        for (j = 0; j < workers_count; j++) {
          if(busy_workers[j] == 0){
            available_nodes++;            
            if(available_nodes == model_cores[i]){
              //printf("%d %d\n", available_nodes, model_cores[i]);
              break;
            }
          }
        }
        if(available_nodes < model_cores[i]){
          if(VERBOSE)
            XBT_INFO("Insuficient workers for task \"%d\" (%d available workers. need %d). Waiting.", i, available_nodes, model_cores[i]);
          //MSG_process_sleep(1.0f);
          MSG_process_suspend(p_master);     
        }               
      }while(available_nodes < model_cores[i]);      

      task_queue[i].numNodes = model_cores[i];
      task_queue[i].startTime = 0.0f;
      task_queue[i].endTime = 0.0f;
      task_queue[i].submitTime = model_submit[i];
      //task_queue[i].task_comp_size = (double*) malloc(model_cores[i] * sizeof(double));
      //task_queue[i].task_comm_size = (double*) malloc(model_cores[i] * model_cores[i] * sizeof(double));
      task_queue[i].task_allocation = (int*) malloc((model_cores[i]) * sizeof(int));      
      //task_queue[i].task_workers = (msg_host_t*) calloc(model_cores[i], sizeof(msg_host_t));

      //tasks_comp_sizes[i] = (double*) malloc(model_cores[i] * sizeof(double));
      //tasks_comm_sizes[i] = (double*) malloc(model_cores[i] * model_cores[i] * sizeof(double));
      //tasks_allocation[i] = (int*) malloc((model_cores[i] + 1) * sizeof(int));
      //tasks_allocation[i][0] = model_cores[i];
      //tasks_workers[i] = xbt_new0(msg_host_t*, model_cores[i]);

      int count = 0;
      for (j = 0; j < workers_count; j++) {          
          if(busy_workers[j] == 0){
            //task_queue[i].task_workers[count] = workers[j];
            task_queue[i].task_allocation[count] = j;
            busy_workers[j] = 1;
            count++;
          }
          if(count >= model_cores[i]){
            break;
          }
      }

      msg_host_t self = MSG_host_self();
      double speed = MSG_host_get_speed(self);

      double comp_size = model_runtimes[i] * speed;
      double comm_size = 1000.0f;//0.001f * MEGA; 

      /*
      for (j = 0; j < model_cores[i]; j++) {
          task_queue[i].task_comp_size[j] = comp_size;
      }

      for (j = 0; j < model_cores[i]; j++)
          for (k = j + 1; k < model_cores[i]; k++)
            task_queue[i].task_comm_size[j * model_cores[i] + k] = comm_size;
      */

      
      char sprintf_buffer[64];
      if(i < NUM_TASKS_STATE){
        sprintf(sprintf_buffer, "Task_%d", i);
      }else{
        sprintf(sprintf_buffer, "Task_%d", orig_task_positions[i - NUM_TASKS_STATE]);
      }
      todo[i] = MSG_task_create(sprintf_buffer, comp_size, comm_size, &task_queue[i]);

      if(VERBOSE)
      XBT_INFO("Dispatching \"%s\" [r=%.1f,c=%d, s=%d]", todo[i]->name, model_runtimes[i], model_cores[i], model_submit[i]);

      MSG_task_send(todo[i], MSG_host_get_name(workers[i]));

      if(VERBOSE)
      XBT_INFO("Sent");

      if(i == NUM_TASKS_STATE - 1){
        t0 = MSG_get_clock();        
        
        if(STATE){
          float* elapsed_times = (float*) calloc(workers_count, sizeof(float));
          for (j = 0; j <= i; j++) {
            if(task_queue[j].endTime == 0.0f){
              float task_elapsed_time = MSG_get_clock() - task_queue[j].startTime;
              if(j == i){
                task_elapsed_time = 0.01f;
              }           
              //printf("%d - %f\n", j, task_elapsed_time);
              for (k = 0; k < model_cores[j]; k++) {
                //printf("%d\n", task_queue[j].task_allocation[k]);
                elapsed_times[(task_queue[j].task_allocation[k])] = task_elapsed_time;
              }
            }
          }
          for (j = 0; j < workers_count; j++) {
            if(j < workers_count - 1)
              printf("%f,", elapsed_times[j]);
            else
              printf("%f\n", elapsed_times[j]);          
          }
          break;
        }
      }       
    }

if(STATE){
  if(VERBOSE)
    XBT_INFO("All tasks have been dispatched. Let's tell everybody the computation is over.");
  for (i = NUM_TASKS_STATE; i < num_managers; i++) {
    msg_task_t finalize = MSG_task_create("finalize", 0, 0, FINALIZE);
    MSG_task_send(finalize, MSG_host_get_name(workers[i]));
  }
}

  if(VERBOSE)
  XBT_INFO("Goodbye now!");
  free(workers);
  free(todo);
  return 0;
  }

}                               /* end_of_master */

/** Receiver function  */
int taskManager(int argc, char *argv[])
{
  msg_task_t task = NULL;
  struct task_t* _task = NULL;
  int i;
  int res;
  //while (1) {
    res = MSG_task_receive(&(task),MSG_host_get_name(MSG_host_self()));
    xbt_assert(res == MSG_OK, "MSG_task_receive failed");
    _task = (struct task_t*) MSG_task_get_data(task);

    if(VERBOSE)
    XBT_INFO("Received \"%s\"", MSG_task_get_name(task));
    
    if (!strcmp(MSG_task_get_name(task), "finalize")) {
      MSG_task_destroy(task);
      return 0;
    }
    

    if(VERBOSE)
    XBT_INFO("Processing \"%s\"", MSG_task_get_name(task));
    /*
    XBT_INFO("Executing on hosts: ");    
    for(i=0;i<_task->numNodes;i++){
      XBT_INFO("\"%s\"", MSG_host_get_name(_task->task_workers[i]));
    }
    */
    _task->startTime = MSG_get_clock();
    MSG_task_execute(task);    
    _task->endTime = MSG_get_clock();
    if(VERBOSE)
    XBT_INFO("\"%s\" done", MSG_task_get_name(task));    
    int* allocation = _task->task_allocation;
    int n = _task->numNodes;
    //int i;
    for(i = 0; i < n; i++){
      busy_workers[allocation[i]] = 0;
    } 
    MSG_task_destroy(task);
    task = NULL;
    MSG_process_resume(p_master);
  //}
  if(VERBOSE)
  XBT_INFO("I'm done. See you!");
  return 0;
}                               /* end_of_worker */

/** Test function */
msg_error_t test_all(const char *platform_file,
                     const char *application_file)
{
  msg_error_t res = MSG_OK;
  int i;

  {                             /*  Simulation setting */
    MSG_config("host/model", "default");
    //MSG_set_channel_number(1);
    MSG_create_environment(platform_file);
  }
  {                             /*   Application deployment */
    //int i;
    
    MSG_function_register("master", master);
    MSG_function_register("taskManager", taskManager);
    
    MSG_launch_application(application_file);

    char sprintf_buffer[64];

    for(i = 0; i < num_managers; i++){
      sprintf(sprintf_buffer, "node-%d", i+1);
      MSG_process_create("taskManager", taskManager, NULL, MSG_get_host_by_name(sprintf_buffer));
    }

  }
  res = MSG_main();
  
  double sumSlowdown = 0.0f;
  slowdown = (double* ) calloc(MODEL_NUM_TASKS, sizeof(double));
  int _count = 0;
  for (i = NUM_TASKS_STATE; i < number_of_tasks; i++) {
    double waitTime = task_queue[i].startTime - task_queue[i].submitTime;
    double runTime = task_queue[i].endTime - task_queue[i].startTime;
    double quocient = runTime >= TAO ? runTime : TAO;
    double slow = (waitTime + runTime) / quocient;  
    slowdown[_count] = slow >= 1.0f ? slow : 1.0f;
    sumSlowdown += slowdown[_count];
    _count++;
    //printf("%f %f\n", task_queue[i].startTime, task_queue[i].endTime);
  }

  double AVGSlowdown = sumSlowdown / MODEL_NUM_TASKS;
  
  if(VERBOSE){
    XBT_INFO("Average bounded slowdown: %f", AVGSlowdown);
    XBT_INFO("Simulation time %g", MSG_get_clock());
  }else if(!STATE){
    printf("%f\n", AVGSlowdown);
  }
//int i,j;

/*
for(i=0;i<MAX_TASKS; i++){
printf("%f,", sched_task_placement[i]);
} 
printf("%g\n", MSG_get_clock());
*/


  return res;
}                               /* end_of_test_all */


/** Main function */
int main(int argc, char *argv[])
{
  msg_error_t res = MSG_OK;

  int i;

  MSG_init(&argc, argv);
  if (argc < 3) {
    printf("Usage: %s platform_file deployment_file [-verbose]\n", argv[0]);
    printf("example: %s msg_platform.xml msg_deployment.xml -verbose\n", argv[0]);
    exit(1);
  }
  //seed = atoi(argv[3]);
  if(argc >= 4){
    for(i = 3;i < argc; i++){
      if (strcmp(argv[i], "-verbose") == 0){
        VERBOSE = 1;
      }
      if (strcmp(argv[i], "-state") == 0){
        STATE = 1;
      }
	  if (strcmp(argv[i], "-lpt") == 0){
        chosen_policy = LPT;
      }
	  if (strcmp(argv[i], "-wfp3") == 0){
        chosen_policy = WFP3;
      }
	  if (strcmp(argv[i], "-unicef") == 0){
        chosen_policy = UNICEF;
      }
      if (strcmp(argv[i], "-c1") == 0){
        chosen_policy = CANDIDATE1;
      }
      if (strcmp(argv[i], "-c2") == 0){
        chosen_policy = CANDIDATE2;
      }
    }
  }
  res = test_all(argv[1], argv[2]);

  if (res == MSG_OK)
    return 0;
  else
    return 1;
}                               /* end_of_main */

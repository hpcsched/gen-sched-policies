#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess

subprocess.call(['python test_sched_perfomrance_model256_runtime.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_model1024_runtime.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_model256_estimate.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_model1024_estimate.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_model256_backfilling.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_model1024_backfilling.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_curie_runtime.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_anl_runtime.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_sdscblue_runtime.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_ctcsp2_runtime.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_hpc2n_runtime.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_sdscsp2_runtime.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_curie_estimate.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_anl_estimate.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_sdscblue_estimate.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_ctcsp2_estimate.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_hpc2n_estimate.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_sdscsp2_estimate.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_curie_backfilling.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_anl_backfilling.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_sdscblue_backfilling.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_ctcsp2_backfilling.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_hpc2n_backfilling.py'], shell=True)

subprocess.call(['python test_sched_perfomrance_sdscsp2_backfilling.py'], shell=True)



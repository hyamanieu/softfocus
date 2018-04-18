# -*- coding: utf-8 -*-
"""
Created on Mon Apr 16 11:49:44 2018

build a tidy data set in a folder where each table is a csv file contaning
time, current, volt, power, and energy variables with 1300 rows.

@author: hy.amanieu
"""

import pandas as pd
import numpy as np
from os.path import join

ROWS = 1300
OHM = 0.1
TIME_CONSTANT = 0.01

index = np.array(range(0,ROWS))


def create_random(dirpath, NoF=16):
    """create NoF files in dirpath containing random measurement data    
    """
    for csv_number in range(16):
        time = index + np.cumsum(np.random.choice([0, 1, 10],#non regular time axis
                                              size=(ROWS,),
                                              replace=True,
                                              p=[0.95,0.04,0.01]))
        #current is a parameter, randomly in/decremented by 10  
        current = np.zeros((ROWS,)) + np.cumsum(np.random.choice([-10, 0, 10],
                                                  size=(ROWS,),
                                                  replace=True,
                                                  p=[0.0005,0.9975,0.002]))
        
        #volt is a time & current dependant parameter
        volt = np.zeros((ROWS,))
        for i in index:
            if i == 0:
                volt[i]=0
            else:
                volt[i] = (volt[i-1] 
                      + (OHM*current[i] - volt[i-1])*TIME_CONSTANT*(time[i]-time[i-1]))
        
        power = current*volt
        energy = np.zeros((ROWS,))
        for i in index:
            if i == 0:
                energy[i]=0
            else:
                energy[i] = (energy[i-1] 
                             + (power[i]*(time[i]-time[i-1])))
        
        df = pd.DataFrame({'time': time,
                           'current': current,
                           'volt': volt,
                           'power':power,
                           'energy':energy})
        df.to_csv(join(dirpath,'sample_'+str(csv_number)+'.csv'),index=False)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 25 14:04:44 2019

@author: marcoaqil
"""
import sys
import os
from session import PRFSession
from datetime import datetime
datetime.now().strftime('%Y-%m-%d %H:%M:%S')
opj = os.path.join

def main():
    subject = sys.argv[1]
    sess =  sys.argv[2]
    # 5 conditions: PRF2R, PRF1R, PRF1S, PRF4R, PRF4F 
    #(2 squares Regular speed, 1 square Regular, 1 square Slow, 4 square Regular, 4 square Fast)
    task = sys.argv[3]
    #in the full experiment we would do 3 runs
    run = sys.argv[4]

    try:
        eye = sys.argv[5]
        if int(eye) == 1:
            eye = True
        else:
            eye = False
    except:
        eye = False

    try:
        delim = sys.argv[6]
        if int(delim) == 1:
            delim = True
        else:
            delim = False
    except:
        delim = False

    output_str = f"{subject}_{sess}_{task}_{run}"
    log_dir = os.path.join(os.getcwd(), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    output_dir = opj(log_dir, f"{output_str}_Logs")
    
    #if os.path.exists(output_dir):
    #    print("Warning: output directory already exists. Renaming to avoid overwriting.")
    output_dir = output_dir + datetime.now().strftime('%Y%m%d%H%M%S')
    
    settings_file = opj(os.getcwd(), f"expsettings_{task[5:]}.yml")
    ts = PRFSession(
        output_str=output_str, 
        output_dir=output_dir, 
        settings_file=settings_file,
        eyetracker_on=eye,
        delimit_screen=delim)

    ts.run()

if __name__ == '__main__':
    main()
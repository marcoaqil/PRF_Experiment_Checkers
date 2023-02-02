#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 25 14:05:10 2019

@author: marcoaqil
"""

import numpy as np
import os
from psychopy import visual
from psychopy.visual import filters
from psychopy import tools
from exptools2.core import PylinkEyetrackerSession
from exptools2.core.session import _merge_settings
from trial import (
    PRFTrial,
    DummyWaiterTrial,
    ScreenDelimiterTrial
)

from stim import PRFStim, DelimiterLines
import yaml
opj = os.path.join

class PRFSession(PylinkEyetrackerSession):
    
    def __init__(self, output_str, output_dir, settings_file, eyetracker_on=True, delimit_screen=False):
        
        super().__init__(output_str, output_dir=output_dir, settings_file=settings_file, eyetracker_on=eyetracker_on)  # initialize parent class!
        
        # set screen delimiter
        self.screen_delimit_trial = delimit_screen

        #if we are scanning, here I set the mri_trigger manually to the 't'. together with the change in trial.py, this ensures syncing
        if self.settings['mri']['topup_scan']:
            self.topup_scan_duration=self.settings['mri']['topup_duration']
        
        if self.settings['PRF_stimulus_settings']['Scanner_sync']:
            self.bar_step_length = self.settings['mri']['TR']
            self.mri_trigger='t'
        else:
            self.bar_step_length = self.settings['PRF_stimulus_settings']['Bar_step_length']
            
        if self.settings['PRF_stimulus_settings']['Screenshot']:
            self.screen_dir = opj(output_dir, f"{output_str}_Screenshots")
            if not os.path.exists(self.screen_dir):
                os.makedirs(self.screen_dir, exist_ok=True)
        
        #create all stimuli and trials at the beginning of the experiment, to save time and resources        
        self.create_stimuli()
        self.create_trials()
            
    def create_stimuli(self):
        
        #generate PRF stimulus
        self.prf_stim = PRFStim(
            session=self, 
            squares_in_bar=self.settings['PRF_stimulus_settings']['Squares_in_bar'], 
            bar_width_deg=self.settings['PRF_stimulus_settings']['Bar_width_in_degrees'],
            flicker_frequency=self.settings['PRF_stimulus_settings']['Checkers_motion_speed'])#self.deg2pix(self.settings['prf_max_eccentricity']))    
        
        #currently unused
        #self.instruction_string = """Please fixate in the center of the screen. Your task is to respond whenever the dot changes color."""

        #generate raised cosine alpha mask
        mask = filters.makeMask(
            matrixSize=self.win.size[0], 
            shape='raisedCosine', 
            radius=np.array([self.win.size[1]/self.win.size[0], 1.0]),
            center=(0.0, 0.0), 
            range=[-1, 1], 
            fringeWidth=0.02
        )

        #adjust mask size in case the stimulus runs on a mac 
        if self.settings['operating_system'] == 'mac':
            mask_size = [self.win.size[0]/2,self.win.size[1]/2]
        else: 
            mask_size = [self.win.size[0],self.win.size[1]]
            
        self.mask_stim = visual.GratingStim(
            self.win, 
            mask=-mask, 
            tex=None, 
            units='pix',                            
            size=mask_size, 
            pos = np.array((0.0,0.0)), 
            color = [0,0,0]
        )

        #as current basic task, generate fixation circles of different colors, with black border
        fixation_radius_deg = self.settings['PRF_stimulus_settings']['Size_fixation_dot_in_degrees']

#        self.fixation_circle = visual.Circle(self.win, 
#            radius=fixation_radius_pixels, 
#            units='pix', lineColor='black')
        
        #two colors of the fixation circle for the task
        self.fixation_disk_0 = visual.Circle(
            self.win, 
            units='deg', 
            radius=fixation_radius_deg, 
            fillColor=[1,-1,-1], 
            lineColor=[1,-1,-1])
        
        self.fixation_disk_1 = visual.Circle(
            self.win, 
            units='deg', 
            radius=fixation_radius_deg, 
            fillColor=[-1,1,-1], 
            lineColor=[-1,1,-1])

        # delimiter stimuli
        if self.screen_delimit_trial:
            self.delim = DelimiterLines(
                win=self.win, 
                color=self.settings['various'].get('cue_color'),
                colorSpace="hex")

    def create_trials(self):
        """creates trials by setting up prf stimulus sequence"""

        # start with dummy if no screen delimiter trial is requested
        dummy_id = -1

        # screen delimiter trial
        self.cut_pixels = {"top": 0, "right": 0, "bottom": 0, "left": 0}
        if self.screen_delimit_trial:

            delimiter_trial = ScreenDelimiterTrial(
                session=self,
                trial_nr=dummy_id,
                phase_durations=[np.inf,np.inf,np.inf,np.inf],
                keys=['b', 'y', 'r'],
                delim_step=self.settings['PRF_stimulus_settings'].get('delimiter_increments'))
            
        
        # Only 1 phase of np.inf so that we can run the fixation task right of the bat
        dummy_trial = DummyWaiterTrial(
            session=self,
            trial_nr=dummy_id,
            phase_durations=[np.inf],
            txt='Waiting for scanner trigger')

        # insert delimiter trial if requested
        self.trial_list = [dummy_trial]
        if self.screen_delimit_trial:
            self.trial_list = [delimiter_trial, dummy_trial]
        
        # track initial number of trials depending on presence of delimiter trial
        #self.dummy_trial_counter = len(self.trial_list)
        
        #simple tools to check subject responses online
        self.correct_responses = 0
        self.total_responses = 0
        self.dot_count = 0
        
        bar_orientations = np.array(self.settings['PRF_stimulus_settings']['Bar_orientations'])
        #create as many trials as TRs. 5 extra TRs at beginning + bar passes + blanks
        self.trial_number = self.settings['PRF_stimulus_settings']['Extra_TRs_beginning'] + self.settings['PRF_stimulus_settings']['Bar_pass_steps']*len(np.where(bar_orientations != -1)[0]) + self.settings['PRF_stimulus_settings']['Blanks_length']*len(np.where(bar_orientations == -1)[0])
  
        print("Expected number of stimulus TRs: %d"%self.trial_number)
        #create bar orientation list at each TR (this can be done in many different ways according to necessity)
        #for example, currently blank periods have same length as bar passes. this can easily be changed here
        steps_array=self.settings['PRF_stimulus_settings']['Bar_pass_steps']*np.ones(len(bar_orientations))
        blanks_array=self.settings['PRF_stimulus_settings']['Blanks_length']*np.ones(len(bar_orientations))
    
        repeat_times=np.where(bar_orientations == -1, blanks_array, steps_array).astype(int)
 
        self.bar_orientation_at_TR = np.concatenate((-1*np.ones(self.settings['PRF_stimulus_settings']['Extra_TRs_beginning']), np.repeat(bar_orientations, repeat_times)))
        
        
        #calculation of positions depend on whether code is run on mac
        if self.settings['operating_system'] == 'mac':
            bar_pos_array = (self.win.size[1]/2)*np.linspace(-0.5,0.5, self.settings['PRF_stimulus_settings']['Bar_pass_steps'])
        else:
            bar_pos_array = self.win.size[1]*np.linspace(-0.5,0.5, self.settings['PRF_stimulus_settings']['Bar_pass_steps'])
        
        blank_array = np.zeros(self.settings['PRF_stimulus_settings']['Blanks_length'])
        
        #the 5 empty trials at beginning
        self.bar_pos_in_ori=np.zeros(self.settings['PRF_stimulus_settings']['Extra_TRs_beginning'])
        
        #bar position at TR
        for i in range(len(bar_orientations)):
            if bar_orientations[i]==-1:
                self.bar_pos_in_ori=np.append(self.bar_pos_in_ori, blank_array)
            else:
                self.bar_pos_in_ori=np.append(self.bar_pos_in_ori, bar_pos_array)
                   
     
        #random bar direction at each step. could also make this time-based
        self.bar_direction_at_TR = np.round(np.random.rand(self.trial_number))
        
        #trial list
        for i in range(self.trial_number):
                
            self.trial_list.append(
                PRFTrial(
                    session=self,
                    trial_nr=i,
                    bar_orientation=self.bar_orientation_at_TR[i],
                    bar_position_in_ori=self.bar_pos_in_ori[i],
                    bar_direction=self.bar_direction_at_TR[i]
                    #,tracker=self.tracker
                )
            )

        #times for dot color change. continue the task into the topup
        self.total_time = self.trial_number*self.bar_step_length 
        
        if self.settings['mri']['topup_scan']==True:
            self.total_time += self.topup_scan_duration

        print(f"expected total duration: {self.total_time}s")
        
        #DOT COLOR CHANGE TIMES    
        self.dot_switch_color_times = np.arange(2.5, self.total_time, float(self.settings['Task_settings']['color_switch_interval']))
        self.dot_switch_color_times += (2*np.random.rand(len(self.dot_switch_color_times))-1)
        
        #needed to keep track of which dot to print
        self.current_dot_time=0
        self.next_dot_time=1
        
        print(self.win.size)

    def draw_stimulus(self):
        #this timing is only used for the motion of checkerboards inside the bar. it does not have any effect on the actual bar motion
        present_time = self.clock.getTime()
        
        #present_trial_time = self.clock.getTime() - self.current_trial_start_time
        prf_time = present_time #/ (self.bar_step_length)
        
  
        #draw the bar at the required orientation for this TR, unless the orientation is -1, code for a blank period
        if self.current_trial.bar_orientation != -1:
            self.prf_stim.draw(
                time=prf_time, 
                pos_in_ori=self.current_trial.bar_position_in_ori, 
                orientation=self.current_trial.bar_orientation,
                bar_direction=self.current_trial.bar_direction)
            
        #hacky way to draw the correct dot color. could be improved
        if self.next_dot_time<len(self.dot_switch_color_times):
            if present_time<self.dot_switch_color_times[self.current_dot_time]:                
                self.fixation_disk_1.draw()
            else:
                if present_time<self.dot_switch_color_times[self.next_dot_time]:
                    self.fixation_disk_0.draw()
                else:
                    self.current_dot_time+=2
                    self.next_dot_time+=2
                    
        #self.fixation_circle.draw()

    def run(self):
        """run the session"""
        # cycle through trials
        # self.display_text('Waiting for scanner', keys=self.settings['mri'].get('sync', 't'))

        if self.eyetracker_on:
            self.calibrate_eyetracker()
            self.start_recording_eyetracker()

        self.start_experiment()
        
        for trial_idx in range(len(self.trial_list)):
            self.current_trial = self.trial_list[trial_idx]
            self.current_trial_start_time = self.clock.getTime()
            print(f"trial {self.current_trial.trial_nr} {self.current_trial_start_time}")

            if self.current_trial.trial_nr == 0:
                print(f"expstart {self.experiment_start_time}")
                self.dot_switch_color_times += self.experiment_start_time
                np.save(opj(self.output_dir, self.output_str+'_DotSwitchColorTimes.npy'), self.dot_switch_color_times)

            self.current_trial.run()
        
        print(f"Expected number of responses: {len(self.dot_switch_color_times)}")
        print(f"Total subject responses: {self.total_responses}")
        print(f"Correct responses (within {self.settings['Task_settings']['response_interval']}s of dot color change): {self.correct_responses}")
        np.save(opj(self.output_dir, self.output_str+'_simple_response_data.npy'), {"Expected number of responses":len(self.dot_switch_color_times),
        														                      "Total subject responses":self.total_responses,
        														                      f"Correct responses (within {self.settings['Task_settings']['response_interval']}s of dot color change)":self.correct_responses})
        
        #print('Percentage of correctly answered trials: %.2f%%'%(100*self.correct_responses/len(self.dot_switch_color_times)))
        
        if self.settings['PRF_stimulus_settings']['Screenshot']==True:
            self.win.saveMovieFrames(opj(self.screen_dir, self.output_str+'_Screenshot.png'))
            
        self.add_settings = {"screen_delim": self.cut_pixels}

        # merge settings
        _merge_settings(self.settings, self.add_settings)

        # write to disk
        settings_out = opj(self.output_dir, self.output_str + '_expsettings.yml')
        with open(settings_out, 'w') as f_out:
            yaml.dump(self.settings, f_out, indent=4, default_flow_style=False)
            
        self.close()

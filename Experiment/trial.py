#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 25 14:06:36 2019

@author: marcoaqil
"""

from exptools2.core.trial import Trial
from psychopy import event
import numpy as np
import os
from psychopy.core import getTime
from psychopy.visual import TextStim
from psychopy import tools
opj = os.path.join
p2d = tools.monitorunittools.pix2deg
d2p = tools.monitorunittools.deg2pix

class PRFTrial(Trial):

    def __init__(self, session, trial_nr, bar_orientation, bar_position_in_ori, bar_direction, *args, **kwargs):
        
        #trial number and bar parameters   
        self.ID = trial_nr
        self.bar_orientation = bar_orientation
        self.bar_position_in_ori = bar_position_in_ori
        self.bar_direction = bar_direction
        self.session=session

        #here we decide how to go from each trial (bar position) to the next.    
        if self.session.settings['PRF_stimulus_settings']['Scanner_sync']:
            #dummy value: if scanning or simulating a scanner, everything is synced to the output 't' of the scanner
            phase_durations = [100]
        else:
            #if not synced to a real or simulated scanner, take the bar pass step as length
            phase_durations = [self.session.settings['PRF_stimulus_settings']['Bar_step_length']] 
            
        #add topup time to last trial
        if self.session.settings['mri']['topup_scan']:
            if self.ID == self.session.trial_number-1:
                phase_durations=[self.session.topup_scan_duration]
            
        super().__init__(session, trial_nr,
            phase_durations, verbose=False,
            *args,
            **kwargs)

    def draw(self, *args, **kwargs):
        # draw bar stimulus and circular (raised cosine) aperture from Session class
        self.session.draw_stimulus() 
        self.session.mask_stim.draw()
        
    def get_events(self):
        """ Logs responses/triggers """
        events = event.getKeys(timeStamped=self.session.clock)
        if events:
            if 'q' in [ev[0] for ev in events]:  # specific key in settings?

                self.session.quit()
 
            for key, t in events:
 
                if key == self.session.mri_trigger:
                    event_type = 'pulse'
                    #marco edit. the second bit is a hack to avoid double-counting of the first t when simulating a scanner
                    if self.session.settings['PRF_stimulus_settings']['Scanner_sync']==True and (t+self.session.experiment_start_time)>0.1:                       
                        self.exit_phase=True
                        #ideally, for speed, would want  getMovieFrame to be called right after the first winflip. 
                        #but this would have to be dun from inside trial.run()
                        if self.session.settings['PRF_stimulus_settings']['Screenshot']:
                            self.session.win.getMovieFrame()
                else:
                    event_type = 'response'
                    self.session.total_responses += 1
                     
                    #tracking percentage of correct responses per session
                    if self.session.dot_count < len(self.session.dot_switch_color_times): 
                        if t > self.session.dot_switch_color_times[self.session.dot_count] and \
                            t < self.session.dot_switch_color_times[self.session.dot_count] + float(self.session.settings['Task_settings']['response_interval']):
                            self.session.correct_responses +=1 
                            # print(f'number correct responses: {self.session.correct_responses}') #testing
                             
                idx = self.session.global_log.shape[0]
                self.session.global_log.loc[idx, 'trial_nr'] = self.trial_nr
                self.session.global_log.loc[idx, 'onset'] = t
                self.session.global_log.loc[idx, 'event_type'] = event_type
                self.session.global_log.loc[idx, 'phase'] = self.phase
                self.session.global_log.loc[idx, 'response'] = key
 
                for param, val in self.parameters.items():
                    self.session.global_log.loc[idx, param] = val
 
                #self.trial_log['response_key'][self.phase].append(key)
                #self.trial_log['response_onset'][self.phase].append(t)
                #self.trial_log['response_time'][self.phase].append(t - self.start_trial)
 
                if key != self.session.mri_trigger:
                    self.last_resp = key
                    self.last_resp_onset = t
        
        #update counter
        if self.session.dot_count < len(self.session.dot_switch_color_times): 
            if self.session.clock.getTime() > self.session.dot_switch_color_times[self.session.dot_count] + \
                float(self.session.settings['Task_settings']['response_interval']): #to give time to respond
                self.session.dot_count += 1   
                # print(f'dot count: {self.session.dot_count}') #testing

class ScreenDelimiterTrial(Trial):

    def __init__(
        self, 
        session, 
        trial_nr, 
        phase_durations=[np.inf,np.inf,np.inf,np.inf], 
        keys=None, 
        delim_step=10, 
        **kwargs):

        super().__init__(
            session, 
            trial_nr, 
            phase_durations, 
            **kwargs)

        self.session = session
        self.keys = keys
        self.increments = delim_step
        self.txt_height = self.session.settings['various'].get('text_height')
        self.txt_width = self.session.settings['various'].get('text_width')

    def draw(self, **kwargs):

        if self.phase == 0:
            txt = """
Use your right INDEX finger (or 'b') to move the bar UP
Use your right RING finger (or 'y') to move the bar DOWN
            

Use your right PINKY (or 'r') to continue to the next stage"""
            self.start_pos = (-self.session.win.size[0]//2,self.session.win.size[1]//3)
            self.session.delim.line1.start = self.start_pos
            self.session.delim.line1.end = (self.session.win.size[0],self.start_pos[1])
        elif self.phase == 1:
            txt = """
Use your right INDEX (or 'b') finger to move the bar RIGHT
Use your right RING (or 'y') finger to move the bar LEFT
            

Use your right PINKY (or 'r') to continue to the next stage"""
            self.start_pos = (self.session.win.size[0]//2.5,-self.session.win.size[1]//2)
            self.session.delim.line1.start = self.start_pos
            self.session.delim.line1.end = (self.start_pos[0],self.session.win.size[1])     
        elif self.phase == 2:
            txt = """
Use your right INDEX (or 'b') finger to move the bar DOWN
Use your right RING (or 'y') finger to move the bar UP
            

Use your right PINKY (or 'r') to continue to the next stage"""
            self.start_pos = (-self.session.win.size[0]//2,-self.session.win.size[1]//3)
            self.session.delim.line1.start = self.start_pos
            self.session.delim.line1.end = (self.session.win.size[0],self.start_pos[1])
        elif self.phase == 3:
            txt = """
Use your right INDEX (or 'b') finger to move the bar LEFT
Use your right RING (or 'y') finger to move the bar RIGHT
            

Use your right PINKY (or 'r') to continue to the experiment"""
            self.start_pos = (-self.session.win.size[0]//2.5,-self.session.win.size[1]//2)
            self.session.delim.line1.start = self.start_pos 
            self.session.delim.line1.end = (self.start_pos[0],self.session.win.size[1])     

        self.text = TextStim(
            self.session.win, 
            txt, 
            height=self.txt_height, 
            wrapWidth=self.txt_width, 
            **kwargs)

        self.session.delim.draw()
        self.text.draw()

    def get_events(self):
        events = super().get_events()

        if self.keys is None:
            if events:
                self.stop_phase()
        else:
            for key, t in events:
                if key == "q":
                    self.stop_phase()
                elif key == "b":
                    if self.phase == 0:
                        self.session.delim.line1.pos[1] += self.increments
                    elif self.phase == 1:
                        self.session.delim.line1.pos[0] += self.increments
                    elif self.phase == 2:
                        self.session.delim.line1.pos[1] -= self.increments
                    elif self.phase == 3:
                        self.session.delim.line1.pos[0] -= self.increments
                elif key == "y":
                    if self.phase == 0:
                        self.session.delim.line1.pos[1] -= self.increments
                    elif self.phase == 1:
                        self.session.delim.line1.pos[0] -= self.increments
                    elif self.phase == 2:
                        self.session.delim.line1.pos[1] += self.increments
                    elif self.phase == 3:
                        self.session.delim.line1.pos[0] += self.increments
                elif key == "r":
                    self.final_position = [self.start_pos[ii]+self.session.delim.line1.pos[ii] for ii in range(len(self.start_pos))]
                    if self.phase == 0:
                        self.session.cut_pixels['top'] = int((self.session.win.size[1]//2) - self.final_position[1])
                    elif self.phase == 1:
                        self.session.cut_pixels['right'] = int((self.session.win.size[0]//2) - abs(self.final_position[0]))
                    elif self.phase == 2:
                        self.session.cut_pixels['bottom'] = int((self.session.win.size[1]//2) - abs(self.final_position[1]))
                    elif self.phase == 3:
                        self.session.cut_pixels['left'] = int((self.session.win.size[0]//2) - abs(self.final_position[0]))

                        print(self.session.cut_pixels)

                    self.stop_phase()             
                    self.session.delim.line1.pos = (0,0)

class InstructionTrial(Trial):
    """ Simple trial with instruction text. """

    def __init__(
        self, 
        session, 
        trial_nr, 
        phase_durations=[np.inf],
        txt=None, 
        keys=None, 
        **kwargs):

        super().__init__(
            session, 
            trial_nr, 
            phase_durations, 
            **kwargs)

        txt_height  = self.session.settings['various'].get('text_height')
        txt_width   = self.session.settings['various'].get('text_width')

        if txt is None:
            txt = '''Press any button to continue.'''

        self.text = TextStim(self.session.win, txt, height=txt_height, wrapWidth=txt_width, **kwargs)
        self.keys = keys

    def draw(self):
        self.text.draw()

    def get_events(self):
        events = super().get_events()

        if self.keys is None:
            if events:
                self.stop_phase()
        else:
            for key, t in events:
                if key in self.keys:
                    self.stop_phase()


class DummyWaiterTrial(InstructionTrial):
    """ Simple trial with text (trial x) and fixation. """

    def __init__(
        self, 
        session, 
        trial_nr, 
        phase_durations=None,
        txt="Waiting for scanner triggers.", **kwargs):

        super().__init__(
            session, 
            trial_nr, 
            phase_durations, 
            txt, 
            **kwargs)

    def draw(self):
        if self.phase == 0:
            self.text.draw()

    def get_events(self):
        events = Trial.get_events(self)

        if events:
            for key, t in events:
                if key == self.session.mri_trigger:
                    if self.phase == 0:
                        self.stop_phase()
                        self.session.experiment_start_time = self.session.clock.getTime()

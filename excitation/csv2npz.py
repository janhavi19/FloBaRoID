#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-

#read data from Przemek's Walk-Man walking csv files

import sys
import os
import argparse
import numpy as np

import matplotlib.pyplot as plt
plt.style.use('seaborn-muted')

import os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from identification.data import Data

from IPython import embed

sampleTime = 0.005

def readCSV(dir, config):
    out = {}
    jointNames = ['R-HIP_R', 'R-HIP_Y', 'R-HIP_P', 'R-KNEE', 'R-ANK_P', 'R-ANK_R', 'L-HIP_R', 'L-HIP_Y', 'L-HIP_P', 'L-KNEE', 'L-ANK_P', 'L-ANK_R', 'WaistLat', 'WaistSag', 'WaistYaw', 'LShSag', 'LShLat', 'LShYaw', 'LElbj', 'LForearmPlate', 'LWrj1', 'LWrj2', 'NeckYawj', 'NeckPitchj', 'RShSag', 'RShLat', 'RShYaw', 'RElbj', 'RForearmPlate', 'RWrj1', 'RWrj2']

    file = os.path.join(dir, 'jointLog.csv')     #joint positions and torques
    f = np.loadtxt(file)
    out['positions'] = np.empty( (f.shape[0], config['N_DOFS']) )
    out['torques'] = np.empty( (f.shape[0], config['N_DOFS']) )
    out['times'] = np.empty( f.shape[0] )
    out['times'][:] = np.arange(0, f.shape[0])*sampleTime

    # generate some empty arrays, will be calculated in preprocess()
    out['velocities'] = np.zeros_like(out['positions'])
    out['accelerations'] = np.zeros_like(out['positions'])

    #plt.rc('text', usetex=True)

    fig = plt.figure()
    ax1 = fig.add_subplot(3,2,1) # three rows, one column, first plot
    ax2 = fig.add_subplot(3,2,2)
    dofs_file = len(f[1])/6
    for dof in range(config['N_DOFS']):
        out['positions'][:, dof] = f[:, dof+dofs_file*2]   #motor encoders
        out['torques'][:, dof] = f[:, dof+dofs_file*4]   #torque sensors
        ax1.plot(out['times'], out['positions'][:, dof], label=jointNames[dof])
        ax2.plot(out['times'], out['torques'][:, dof], label=jointNames[dof])

    file = os.path.join(dir, 'feedbackData.csv')  #force torque and IMU
    f = np.loadtxt(file)
    out['FTleft'] = np.empty( (f.shape[0], 6) )   #FT left foot, 3 force, 3 torque values
    out['FTright'] = np.empty( (f.shape[0], 6) )   #FT right foot
    out['IMUrpy'] = np.empty( (f.shape[0], 3) )   #IMU orientation, r,p,y
    ax3 = fig.add_subplot(3,2,3)
    rpy_labels = ['r','p', 'y']
    for i in range(0,3):
        out['IMUrpy'][:, i] = f[:, i]
        ax3.plot(out['times'], out['IMUrpy'][:, i], label=rpy_labels[i])

    ax4 = fig.add_subplot(3,2,4)
    ax5 = fig.add_subplot(3,2,5)
    ft_labels = ['F_x', 'F_y', 'F_z', 'M_x', 'M_y', 'M_z']
    for i in range(0,6):
        out['FTleft'][:, i] = f[:, 3+i]
        out['FTright'][:, i] = f[:, 3+6+i]
        ax4.plot(out['times'], out['FTleft'][:, i], label=ft_labels[i])
        ax5.plot(out['times'], out['FTright'][:, i], label=ft_labels[i])

    #set titles and enable legends for each subplot
    t = ['positions', 'torques', 'IMU', 'FT left', 'FT right']
    for i in range(0,5):
        plt.subplot(321+i)
        eval('ax{}'.format(1+i)).legend(loc='best', fancybox=True, fontsize=10, title='')
        plt.title(t[i])

    fig.tight_layout()

    plt.show()

    return out

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Load measurements from csv and write as npz.')
    #parser.add_argument('--config', required=True, type=str, help="use options from given config file")
    parser.add_argument('--measurements', required=True, type=str, help='the directory to load the measurements from')
    parser.add_argument('--outfile', type=str, help='the filename to save the measurements to')
    parser.set_defaults(outfile='measurements.npz')
    args = parser.parse_args()

    config = {}
    config['N_DOFS'] = 6   #walkman leg
    config['useDeg'] = False

    out = readCSV(args.measurements, config)
    out['frequency'] = 1.0/sampleTime
    data = Data(config)
    data.preprocess(Q=out['positions'], V=out['velocities'], Vdot=out['accelerations'],
                    Tau=out['torques'], T=out['times'], Fs=out['frequency'])

    np.savez(args.outfile, out)
    print("Saved csv data as as {}".format(args.outfile))
    print "Samples: {}, Time: {}s, Frequency: {} Hz".format(out['times'].shape[0], out['times'][-1], out['frequency'])
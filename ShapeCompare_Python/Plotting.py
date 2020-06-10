# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 12:32:24 2020

@author: temp
"""
import matplotlib.pyplot as plt
import itertools
#import os


def plot_geometry_comparison(Alldf, bldgname, figpath=None, savefig=None, dpi=300, color=None):
    
    plt.style.use('seaborn-darkgrid')
    
    fig, axes = plt.subplots(2,2, sharex=True)
    axes = list(itertools.chain(*axes))
    
    colnamedic= {'Window': 'Exterior Window Area {m2}',
                 'Wall'  : 'Exterior Net Wall Area {m2}',
                 'Floor' : 'Floor Area {m2}',
                 'Volume': 'Volume {m3}'}
        
    ax_count=0
    for key, val in colnamedic.items():
        ax = axes[ax_count]
        temp_ser = Alldf.xs(val, axis=1, level=1).sum()
        
        print('\n', val)
        print(temp_ser)
        
        if color:
            temp_ser.plot(kind='bar', ax=ax, figsize=(8,4), rot=40, color=color) #title=val,
        else:
            temp_ser.plot(kind='bar', ax=ax, figsize=(8,4), rot=40) #title=val,

        ax.set_title(val, fontweight='normal')
        
        refheight = ax.patches[0].get_height()
        for patch_count, rect in enumerate(ax.patches):
            difftxt = int(100*(rect.get_height() - refheight) / refheight)

            if abs(difftxt)>=30: weight='heavy'
            else: weight='normal'
            
            if difftxt>= 0:
                difftxt = '+' + str(difftxt) + '%'
            elif difftxt < 0:
                difftxt = str(difftxt) + '%'

            if rect.get_height() == 0:
                difftxt = 'Simulation\nfailed'
                ypos = 0.1*ax.get_ylim()[1]
                annocolor= 'black'
                weight = 'normal'
                va = 'bottom'
                rot = 90
            else:
                ypos = rect.get_height()*0.9
                annocolor = 'white'
                va = 'top'
                rot = 0                
                
            if patch_count==0: difftxt='Refer\n-ence'
            
            ax.annotate(difftxt,
                        xy = (rect.get_x() + rect.get_width()/2, ypos), 
                        horizontalalignment = 'center',
                        verticalalignment = va,
#                        xycoords = xycoords,
                        rotation = rot,
                        color=annocolor, fontweight=weight)
        ax_count+=1
    
    plt.subplots_adjust(hspace = 0.4)
    plt.suptitle(bldgname, fontweight='normal', y=1.0, fontsize=15)

    if savefig:
        plt.savefig(figpath, dpi=dpi, bbox_inches='tight')

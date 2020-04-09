# -*- coding: utf-8 -*-
"""    
Created on Tue Feb 18 13:13:54 2020

@author: temp
"""

import pandas as pd
from eppy.results import readhtml
import matplotlib.pyplot as plt
import locale #to handle thousands separator.
import itertools
import os

#def convert_to_metric(orig_df):
#    
#    df = orig_df.copy(deep=True)
#    
#    df['Floor Area {ft2}'] = df['Floor Area {ft2}'] * 0.092903 # convert ft2 to m2
#    df['Volume {ft3}'] = df['Volume {ft3}'] * 0.0283168 # convert ft3 to m3
#    df['Exterior Gross Wall Area {ft2}'] = df['Exterior Gross Wall Area {ft2}'] * 0.092903 # convert ft2 to m2
#    df['Exterior Net Wall Area {ft2}'] = df['Exterior Net Wall Area {ft2}'] * 0.092903 # convert ft2 to m2
#    df['Exterior Window Area {ft2}'] = df['Exterior Window Area {ft2}'] * 0.092903 # convert ft2 to m2
#
#    df.rename(columns={'Floor Area {ft2}':'Floor Area {m2}',
#                       'Volume {ft3}':'Volume {m3}',
#                       'Exterior Gross Wall Area {ft2}':'Exterior Gross Wall Area {m2}',
#                       'Exterior Net Wall Area {ft2}':'Exterior Net Wall Area {m2}',
#                       'Exterior Window Area {ft2}':'Exterior Window Area {m2}'},
#              inplace=True)
#    return df


def retain_useful_cols(df):
    colnames = ['Floor Area {m2}',
                'Volume {m3}',
                'Exterior Net Wall Area {m2}',
                'Exterior Window Area {m2}']
    
    return df[colnames]
    

def get_zoneinformation_from_html_report(html_report_path):
    
    filehandle = open(html_report_path, 'r').read()
    ltables = readhtml.lines_table(filehandle)
    
    InitSummary = [ltable for ltable in ltables if 'Zone Information'  in ltable[0]]
    df = pd.DataFrame(InitSummary[0][1])
    
    df.columns = df.iloc[0,:]
    df.index = df.iloc[:,1]
    df = df.iloc[1:,:]

    return df


def result_paths_to_dataframes(*paths):
    '''This function is intended to read in ZoneInformation report from an EnergyPlus run.
    If .htm or .html reports are available then input the paths directly into function argument.
    Otherewise if ZoneInformation reports are not available in .htm or .html, then copy-paste into excel and reference the excel path
    (Format in Excel should be, 'ZoneInformation' title on the first cell, second row left blank, then the table itself starting on A3.)
    This function detects file extensions and convert them into dataframes accordingly.'''

    dfs = list()
    for path in paths:
        if 'xlsx' in path.split('.')[-1]:
            print('reading excel...: {}'.format(path))
            df = pd.read_excel(path, skiprows=2, index_col=1)

        elif 'html' in path.split('.')[-1] or 'htm' in path.split('.')[-1]:
            print('reading html...: {}'.format(path))
            df = get_zoneinformation_from_html_report(path)
        else:
            raise "check file names or extensions. Extensions must end in one of: xlsx, htm, html."
        
#        # if the results are in imperial, then convret to metric.
#        if any('ft2' in colname for colname in df.columns): df = convert_to_metric(df)
        
        dfs.append(retain_useful_cols(df))
        
    return dfs


#%% BIM geometry functions
def filter_by_function(dfs, retain_col='Exterior'):
    for key, df in dfs.items():
        try:
            dfs[key] = df[df['Function']=='Exterior']
            print(key + " has a Function column.")
        except: 
            print(key + " has no Function column.")

    return dfs



def drop_na_rows(dfs):
    for key, df in dfs.items():
        df.dropna(how='all', axis=0, inplace=True)
    return dfs


def Make_BIM_area_df_from_dfs(dfs):
    BIM_df = pd.DataFrame()
    for key, df in dfs.items():
        
        if 'Space' in key in key:

            spaces_i = pd.DataFrame(df['Volume'])
            spaces_i.columns = ['Volume']

            BIM_df = pd.concat([BIM_df, spaces_i], axis=1, sort=False)

        #construct separate dataframe with 'Area' information.
        if 'Area' in df.columns:
            # append 'Area' column of each dataframe to BIM_srfs
            areas_i = pd.DataFrame(df['Area'])
            areas_i.columns = [key] # rename the column handle

            BIM_df = pd.concat([BIM_df, areas_i], axis=1, sort=False)
            
    return BIM_df.applymap(remove_units)



def remove_units(i): # use only if every cell containing units is separated by a space.
    if type(i)==str:
        i = i.split(" ")[0]
        try: i = locale.atof(i) # convert to float, while taking care of thousands operators
        except: return i
    return i

def Remove_keyword_from_col_names(BIMdf, keyword):

    BIMdf.columns = [col.split(keyword)[0] for col in BIMdf.columns] # get rid of keyword from column names
    return BIMdf

def Make_aggregated_BIMsurface_df(BIMdf):
    BIM_srfs_tbl = pd.merge(left = BIMdf.sum().to_frame(name='sum'),
                            right = BIMdf.count().to_frame(name='count'),
                            left_index=True,
                            right_index=True)
    
    return BIM_srfs_tbl


def make_column_names_compatible(BIMdf):
    colnamedic= {'Window': 'Exterior Window Area {m2}',
                 'Wall'  : 'Exterior Net Wall Area {m2}',
                 'Floor' : 'Floor Area {m2}',
                 'Volume': 'Volume {m3}'}

    return BIMdf[list(colnamedic.keys())].rename(columns=colnamedic)


def deal_with_curtain_walls(dfs, action='remove', keyword=None):
    walldf = dfs['Wall'+keyword]
    CurtainWallAreadf = walldf[walldf.Family=='Curtain Wall'].loc[:,'Area'].to_frame()
    
    # curtain wall areas come embedded in Wall schedule.
    if action=='lump_to_wall':
        print('Curtain wall areas are being lumped to wall area.')
        return dfs
    
    elif action == 'lump_to_window':
        dfs['Wall'+keyword] = walldf.drop(index = CurtainWallAreadf.index)
        dfs['Window'+keyword] = pd.concat([dfs['Window'+keyword],CurtainWallAreadf], axis=0, ignore_index=True)
        print('Curtain walls areas are being lumped to window area.')
        return dfs
    
    elif action == 'remove':
        dfs['Wall'+keyword] = walldf.drop(index = CurtainWallAreadf.index)
        return dfs
        
    else: raise "action argument must be one of 'lump_to_wall', 'lump_to_window' or 'remove'."

def deal_with_windows(dfs, mullion_width, keyword=None):
    windf = dfs['Window'+keyword]
    windf.loc[:,'Area'] = (windf.loc[:,'Width']-mullion_width) * (windf.loc[:,'Height']-mullion_width)
    dfs['Window'+keyword] = windf
    return dfs


def deal_with_doors(dfs, action=None, keyword=None):
    doordf = dfs['Door'+keyword]
    doorAreadf = (doordf.loc[:,'Width']*doordf.loc[:,'Height']).to_frame(name='Area')
#    doorAreadf = _add_area_column_from_width_and_height_cols(doordf)['Area'].to_frame()
    
    if action == 'lump_to_window' or action==1:
        dfs['Door'+keyword] = doordf.drop(index = doorAreadf.index)
        dfs['Window'+keyword] = pd.concat([dfs['Window'+keyword], doorAreadf], axis=0, ignore_index=True, sort=False)
        print('Door areas are being lumped to Windows')
        return dfs
        
    elif action == 'remove' or action==2:
        dfs['Door'+keyword] = doordf.drop(index = doorAreadf.index)
        return dfs
        
    else: raise "action argument must be one of 'lump_to_window' or 'remove'."


def deal_with_curtain_panels(dfs, action='lump_to_wall', family_filter_strs=None, reverse_filter:bool=False, keyword=None, mullion_width=0):
    '''Input a string or a list of strings to filter with. if nothing is input, then no filter is applied.
    
    action              = 'lump_to_wall', 'lump_to_window', 'remove'
    family_filter_strs  = None, 'string', or ['string1', 'string2', ...]
    reverse_filter      = False, True
    '''
        
    paneldf = dfs['Panel'+keyword]
    
    if family_filter_strs == None:
        pass
    elif type(family_filter_strs) == str:
        regex_str = family_filter_strs
        mask = paneldf['Family'].str.contains(regex_str, regex=True, case=True)
    elif type(family_filter_strs) == list:
        regex_str = '|'.join(map(str, family_filter_strs))
        mask = paneldf['Family'].str.contains(regex_str, regex=True, case=True)
    else: raise "'family_filter_strs' argument expects one of: None, a string, or a list of strings"
    
    
    paneldf['Area'] = (paneldf['Width'] - (mullion_width*2)) * (paneldf['Height'] - (mullion_width*2))
    
    if family_filter_strs == None:
        filtereddf = paneldf['Area'].to_frame()
        print('No filtering applied to curtain panels.')
    elif reverse_filter==False:
        filtereddf = paneldf[~mask]['Area'].to_frame()
        print('Filtering out the curtain panels containing {} in Family strings'.format(family_filter_strs))
    elif reverse_filter==True:
        filtereddf = paneldf[mask]['Area'].to_frame()
        print('Filtering out the curtain panels NOT containing {} in Family strings'.format(family_filter_strs))
    else: raise "'reverse_filter' argument expects a boolean input."
        
    # lump panel areas onto either wall or window areas
    if action=='lump_to_wall':
        dfs['Wall'+keyword] = pd.concat([dfs['Wall'+keyword], filtereddf], axis=0, ignore_index=True, sort=False)
        print('Curtain panel areas are lumped onto Wall Areas.')
    elif action=='lump_to_window':
        dfs['Window'+keyword] = pd.concat([dfs['Window'+keyword], filtereddf], axis=0, ignore_index=True, sort=False)
        print('Curtain panel areas are lumped onto Window Areas.')
    elif action=='remove':
        print('Curtain panel areas will not be accounted for.')
    else: raise "'action' argument must be one of: 'lump_to_wall', 'lump_to_window', or 'remove'."
    
    # empty the Curtain Panel dataframe
    dfs['Panel'+keyword] = dfs['Panel'+keyword][0:0]
    
    return dfs

def curtain_wall_and_panel_conflict_check(curtain_wall_action, curtain_panel_action):
    if curtain_wall_action!='remove' and curtain_panel_action!='remove':
        raise "One of 'curtain wall action' and 'curtain panel action' must be 'remove', otherwise the areas will be double-counted."
        
    elif curtain_wall_action == 'remove' and curtain_panel_action == 'remove':
        print('\n***Warning - neither curtain wall area or curtain panel area will be accounted for.')

# Plotting
        
def plot_geometry_comparison(Alldf, colnamedic, bldgname, figpath=None, savefig=None, dpi=300, color=None):
    
    plt.style.use('seaborn-darkgrid')
    
    fig, axes = plt.subplots(2,2, sharex=True)
    axes = list(itertools.chain(*axes))
    
    ax_count=0
    for key, val in colnamedic.items():
        ax = axes[ax_count]
        temp_ser = Alldf.xs(val, axis=1, level=1).sum()
        
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
                difftxt = 'Simul-\nation\nfailed'
                ypos = 0.1*ax.get_ylim()[1]
                annocolor= 'black'
                weight = 'normal'
                va = 'bottom'
            else:
                ypos = rect.get_height()*0.9
                annocolor = 'white'
                va = 'top'                
                
            if patch_count==0: difftxt='Refer\n-ence'
            
            ax.annotate(difftxt,
                        xy = (rect.get_x() + rect.get_width()/2, ypos), 
                        horizontalalignment = 'center',
                        verticalalignment = va,
#                        xycoords = xycoords,
                        color=annocolor, fontweight=weight)
        ax_count+=1
    
    plt.subplots_adjust(hspace = 0.4)
#    plt.suptitle(bldgname, fontweight='normal', y=1.0, fontsize=15)

    if savefig:
        
        try: os.mkdir('Figures')
        except: pass
        
        plt.savefig(figpath, dpi=dpi, bbox_inches='tight')


#%% MAIN
def main(keyword,
        bldgname,
        BIM_excel_path,
        BEMkeys,
        BEMpaths,
        filter_out_interior_elements=False,
        window_mullion_width=0,
        door_action='lump_to_window',
        curtain_wall_action='remove',
        curtain_panel_action='lump_to_window',
        panel_mullion_width=0,
        family_filter_strs=None,
        savefig=None,
        figpath=None,
        color=None
        ):

    colnamedic= {'Window': 'Exterior Window Area {m2}',
                 'Wall'  : 'Exterior Net Wall Area {m2}',
                 'Floor' : 'Floor Area {m2}',
                 'Volume': 'Volume {m3}'}
    
    # Input fool-proofing
    curtain_wall_and_panel_conflict_check(curtain_wall_action, curtain_panel_action)
    
    # read in BEM geometry from .xlsx or .htm (or .html)
    print('\n* Reading in EnergyPlus outputs...')
    BEMdfs = result_paths_to_dataframes(*BEMpaths)
    
    # read in BIM geometry
    print('\n* Reading in BIM geometry information from excel...')
    dfs = pd.read_excel(BIM_excel_path, sheet_name=None, header= 0) # reads in every sheet and saves as an OrderedDict of dataframes.
    dfs = drop_na_rows(dfs)
    
    print('\n* Removing Total rows...')
    for key, df in dfs.items():
        print(type(df))
        df.dropna(axis=0, how='any', inplace=True)
    
    # filter items by 'Interior' function.
    if filter_out_interior_elements:
        print("\n* Filtering out elements with function: 'Interior'..." )
        dfs = filter_by_function(dfs, retain_col='Exterior')
    
    print('\n* Dealing with Windows...')
    dfs = deal_with_windows(dfs, mullion_width=window_mullion_width, keyword=keyword)
    
    print('\n* Dealing with Doors...')
    dfs = deal_with_doors(dfs, action=door_action, keyword=keyword)

    print('\n* Dealing with Curtain Walls...')
    dfs = deal_with_curtain_walls(dfs, action=curtain_wall_action, keyword=keyword)

    print('\n* Dealing with Curtain Panels...')
    dfs = deal_with_curtain_panels(dfs, action=curtain_panel_action, mullion_width = panel_mullion_width,
                                   family_filter_strs=family_filter_strs, keyword=keyword)
    
    print('\n* Processing BIM geometry...')
    BIMdf = Make_BIM_area_df_from_dfs(dfs)
    BIMdf = Remove_keyword_from_col_names(BIMdf, keyword=keyword)
    BIMdf = make_column_names_compatible(BIMdf)
    
    print('\n* Reconciling BIM and BEM geometric info...')    
    Allkeys = ['BIM_Geo'] + BEMkeys
    Alldfs = [BIMdf.sum().to_frame(name='BIM_Geo').T] + BEMdfs
    Alldf = pd.concat(Alldfs, axis=1, keys=Allkeys, sort=True)
    
    print('\n* Plotting...')
    plot_geometry_comparison(Alldf, colnamedic, bldgname, figpath=figpath, savefig=savefig, color=color)
    
    return Alldf

#%%
#    
locale.setlocale(locale.LC_ALL, 'en_us.UTF-8')
filter_out_interior_elements = True
keyword = '_SY'
#colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']


bldgname = 'Low Complexity Building (Northern Nomad)'
window_mullion_width = 0.03
door_action = 'remove'
family_filter_strs = None
curtain_wall_action = 'remove'
curtain_panel_action = 'remove'
panel_mullion_width = 0
BEM_path1 = r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\GeometryExport\Approach1_Nomad.xlsx'
BEM_path2 = r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\EUIcomparison\Nomad\Approach2\\Nomad_Approach2_modTable.html'
BEM_path3 = r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\EUIcomparison\Nomad\Approach3\\Nomad_Approach3_modTable.html'
BIM_excel_path = r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\GeometryExport\BIM_Nomad.xlsx'
BEMkeys = ['Approach1','Approach2','Approach3']
BEMpaths = [BEM_path1, BEM_path2, BEM_path3]
color = None
          
#          
#bldgname = 'Medium Complexity Building (Privanzas)'
#window_mullion_width = 0.03
#door_action = 'lump_to_window'
#family_filter_strs = None
#curtain_wall_action = 'remove'
#curtain_panel_action = 'lump_to_window'
#panel_mullion_width = 0.11
#BEM_path1 = r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\GeometryExport\Approach1_Privanzas.xlsx'
#BEM_path2 = r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\EUIcomparison\Privanzas\Approach2\\Privanzas_Approach2_modTable.html'
#BEM_path3 = r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\EUIcomparison\Privanzas\Approach3\\Privanzas_Approach3_modTable.html'
#BIM_excel_path = r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\GeometryExport\BIM_Privanzas.xlsx'
#BEMkeys = ['Approach1','Approach2','Approach3']
#BEMpaths = [BEM_path1, BEM_path2, BEM_path3]
#color = None
#
#bldgname = 'High Complexity Building (EVE Park)'
#window_mullion_width = 0.05
#door_action = 'remove'
#family_filter_strs = ['Empty','Sloped']
#curtain_wall_action = 'remove'
#curtain_panel_action = 'lump_to_wall'
#panel_mullion_width = 0
#BEM_path1 = r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\GeometryExport\Approach1_EVE.xlsx'
#BEM_path2 = r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\GeometryExport\Approach2_EVE_empty.xlsx'
#BEM_path3 = r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\EUIcomparison\EVE\Approach3\EVE_Approach3_modTable.html'
#BIM_excel_path = r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\GeometryExport\BIM_EVE.xlsx'
#BEMkeys = ['Approach1','Approach2','Approach3']
#BEMpaths=[BEM_path1, BEM_path2, BEM_path3]
#color = None



savefig=True
figpath = r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\GeometryExport\Geo_{}.png'.format(bldgname)
#%% RUN: read geometry and plot
    
# Make sure to appropriately filter schedules in Revit. Use m2 for area, m3 for volume, and mm for length.
# 'Exterior' and 'Interior' Wall and Floor functions must be configured correctly.
# Interior windows will count as 'Exterior' window.
# use window mullion width in m.
# when lumping curtain walls to windows mullion area cannot be discounted from window area. 



Alldf = main(keyword = keyword,
             bldgname = bldgname,
             BIM_excel_path = BIM_excel_path,
             BEMkeys = BEMkeys,
             BEMpaths = BEMpaths,
             filter_out_interior_elements = filter_out_interior_elements,
             window_mullion_width = window_mullion_width,
             door_action = door_action,
             curtain_wall_action = curtain_wall_action,
             curtain_panel_action = curtain_panel_action,
             panel_mullion_width = panel_mullion_width,
             family_filter_strs = family_filter_strs,
             savefig = savefig,
             figpath = figpath,
             color = color
             )


#%% Process dataframe, to get geometric deviation by percentage
import numpy as np

#Alldfs.to_pickle(r'C:Users\tempDocumentsCarleton_GradStudiesThesisRevitModelsGeometryExportAllthreedfs.pkl')
Alldfs = pd.read_pickle(r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\GeometryExport\Allthreedfs.pkl')
approaches = ['Approach1', 'Approach2','Approach3']
categories = ['Exterior Net Wall Area {m2}', 'Exterior Window Area {m2}', 'Floor Area {m2}', 'Volume {m3}']
bldgs = ['Nomad', 'Privanzas', 'EVE']
complexities = ['Low']*3 + ['Med']*3 + ['High']*3

for bldg in bldgs:
    for approach in approaches:
        for category in categories:
            orig_val = Alldfs.loc[(bldg,'BIM_Geo',category)][0]
            approach_val = Alldfs.loc[(bldg,approach,category)][0]
            
            if int(approach_val)==0:
                Alldfs.loc[(bldg,approach,category),'deviation'] = 0
                Alldfs.loc[(bldg,approach,category),'dev_percent'] = 0
                print('hit dat')
            else:
                Alldfs.loc[(bldg,approach,category),'deviation'] = approach_val - orig_val
                Alldfs.loc[(bldg,approach,category),'dev_percent'] = 100 * (approach_val - orig_val) / orig_val

devdf = Alldfs['dev_percent'].dropna()

#%% plot summary geometric deviations

for category in categories:

    figsize=(10,4)
    fig, ax = plt.subplots(1, figsize=figsize)
    width=figsize[0]/50
    
    x = np.arange(len(approaches))
    x_labels = approaches
    ax.bar(x-width, devdf.xs(category,level=2).loc[bldgs[0]], width=width, color=['C1','C2','C3'], edgecolor='white')
    ax.bar(x, devdf.xs(category,level=2).loc[bldgs[1]], width=width, color=['C1','C2','C3'], edgecolor='white')
    ax.bar(x+width, devdf.xs(category,level=2).loc[bldgs[2]], width=width, color=['C1','C2','C3'], edgecolor='white')
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.set_ylabel('Geometric Deviation\nfrom Reference (%)', fontsize=13)
    
    ax.set_xlabel(None)
    ax.set_ylim([-65,30])
    
    ax.tick_params(axis='both', which='major', labelsize=13)

    
    highest = max([rect.get_height() for rect in ax.patches])
    lowest = min([rect.get_height() for rect in ax.patches])
    
    for counter, (rect, complexity) in enumerate(zip(ax.patches, complexities)):
        difftxt = int(rect.get_height())
        
        if abs(difftxt)>=30: weight='heavy'
        else: weight='normal'
        
        if difftxt > 0:
            difftxt = '+' + str(difftxt) + '%'
            ha = 'top'
            sign = 1
            color='white'
        elif difftxt < 0:
            difftxt = str(difftxt) + '%'
            ha = 'bottom'
            sign = -1
            color='white'
        elif difftxt == 0:
            difftxt = "simul-\nation\nfailed"
            color='k'
        
        # annotate percentage on each bar
        ax.annotate(difftxt,
                    xy = (rect.get_x() + rect.get_width()/2, rect.get_height()*0.90), 
                    horizontalalignment = 'center',
                    verticalalignment = ha,
                    color=color, fontweight=weight, fontsize=figsize[0]*1.3)
        
        # specify model complexity
        ax.annotate(complexity,
                    xy = (rect.get_x() + rect.get_width()/2, 28),
                    xycoords = 'data',
                    horizontalalignment = 'center',
                    verticalalignment = 'top',
                    fontsize=figsize[0]*1.3)
        
#    plt.suptitle(category, fontsize=figsize[0]*1.3)
    plt.savefig(f'{category}.png', bbox_inches='tight', dpi=300)
#    plt.show




#%% LEGACY
#bldgs = ['Nomad', 'Privanzas', 'EVE']
#titles = ['Low-Complexity Model','Medium-Complexity Model','High-Complexity Model']
#cats = ['Exterior Net Wall Area {m2}', 'Exterior Window Area {m2}', 'Floor Area {m2}', 'Volume {m3}']
#
#plt.style.use('seaborn-darkgrid')
#fig, ax = plt.subplots(len(cats),len(bldgs), figsize=(13,13), dpi=150)
#plt.subplots_adjust(hspace=.6)
#for i, cat in enumerate(cats):
#    dfi = AllSum.xs(cat, level=2)
#    for j, bldg in enumerate(bldgs):
#        dfi.xs(bldg).plot(kind='bar', ax=ax[i,j], rot=20)
#        ax[i,j].set_xlabel(None)
#        
#        if i==0:
#            ax[i,j].set_title(titles[j], y=1.3, fontsize=15)
#        
#        if j==0:
#            pos = ax[i,j].get_position()
#            ylims = ax[i,j].get_ylim()
#            ax[i,j].text(-1, (ylims[1])*1.1, s=cats[i], verticalalignment='bottom', ha='left', fontsize=13, fontweight='heavy')
#
#
#        refheight = ax[i,j].patches[0].get_height()
#        for patch_count, rect in enumerate(ax[i,j].patches):
#            difftxt = int(100*(rect.get_height() - refheight) / refheight)
#            
#            if abs(difftxt)>=30: weight='heavy'
#            else: weight='normal'
#            
#            if difftxt >= 0: difftxt = '+' + str(difftxt) + '%'
#            elif difftxt < 0: difftxt = str(difftxt) + '%'
#            
#            if patch_count==0: difftxt='Refer\n-ence'
#            
#            ax[i,j].annotate(difftxt,
#                        xy = (rect.get_x() + rect.get_width()/2, rect.get_height()*0.9), 
#                        horizontalalignment = 'center',
#                        verticalalignment = 'top',
#                        color='white', fontweight=weight)

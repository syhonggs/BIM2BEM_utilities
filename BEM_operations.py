# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 11:07:56 2020
@author: temp
"""
import pandas as pd
from eppy.results import readhtml

#%% BEM operations
                    
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

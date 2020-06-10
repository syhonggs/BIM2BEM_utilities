# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 11:07:56 2020
@author: temp
"""
import locale #to handle thousands separator.
import pandas as pd

#%% BIM operations

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
   
def remove_units(i): # use only if every cell containing units is separated by a space.
    if type(i)==str:
        i = i.split(" ")[0]
        try: i = locale.atof(i) # convert to float, while taking care of thousands operators
        except: return i
    return i

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

def deal_with_windows(dfs, keyword, mullion_width):

#    print("keyword is: ", keyword)
    windf = dfs['Window'+keyword]
    windf.loc[:,'Area'] = (windf.loc[:,'Width']-mullion_width) * (windf.loc[:,'Height']-mullion_width)
    dfs['Window'+keyword] = windf
    return dfs

def deal_with_doors(dfs, keyword, action=None):
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


def deal_with_curtain_walls(dfs, keyword, action='remove'):
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


def deal_with_curtain_panels(dfs, keyword, action='lump_to_wall', family_filter_strs=None, reverse_filter:bool=False, mullion_width=0):
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

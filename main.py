# -*- coding: utf-8 -*-
"""    
Created on Tue Feb 18 13:13:54 2020

@author: temp
"""

import pandas as pd
#import locale #to handle thousands separator.

import ShapeCompare.BIM_operations as BIM
import ShapeCompare.BEM_operations as BEM
import ShapeCompare.Plotting as Plotting

class Project():
    BIMs = list()
    BEMs = list()

    # Toggles for meta settings
    def name(self, name:str):
        self.name = name

    def keyword(self, keyword:str):
        self.keyword = keyword
        
    def savefig(self, savefig:bool):
        self.savefig = savefig
        
    def figpath(self, figpath:str):
        self.figpath = figpath
  
    # BIM related
    def BIM_add(self, path:str):
        self.BIMs.append(path)


    # BIM processing option toggles
    def BIM_filter_out_interior_elements(self, toggle:bool = False):
        self.BIM_filter_out_interior_elements = toggle

    def BIM_window_mullion_width(self, width:float = 0):
        self.BIM_window_mullion_width = width
        
    def BIM_door_action(self, action:str = 'lump_to_window'):
        """Available options: 'remove', 'lump_to_window'"""
        self.BIM_door_action = action

    def BIM_curtain_wall_action(self, action:str = 'remove'):
        """Available options: 'remove', 'lump_to_wall', 'lump_to_window'"""
        self.BIM_curtain_wall_action = action 

    def BIM_curtain_panel_action(self, action:str = 'lump_to_window'):
        """Available options: 'remove', 'lump_to_wall', 'lump_to_window'"""
        self.BIM_curtain_panel_action = action

    def BIM_panel_mullion_width(self, width:float = 0):
        self.BIM_panel_mullion_width = width

    def BIM_family_filter_strs(self, filterstring = None):
        self.BIM_familily_filter_strs = filterstring



    # BEM related
    def BEM_add(self, description:str, path:str):
        self.BEMs.append([description, path])


#     Main execution
    def execute(self):
        keyword = self.keyword
        
        # Input fool-proofing
        BIM.curtain_wall_and_panel_conflict_check(self.BIM_curtain_wall_action, self.BIM_curtain_panel_action)
        
        # read in BEM geometry from .xlsx or .htm (or .html)
        print('\n* Reading in EnergyPlus outputs...')
        BEMdfs = BEM.result_paths_to_dataframes(*[BEM[1] for BEM in self.BEMs])
        
        # read in BIM geometry
        print('\n* Reading in BIM geometry information from excel...')
        dfs = pd.read_excel(self.BIMs[0], sheet_name=None, header= 0) # reads in every sheet and saves as an OrderedDict of dataframes.
        dfs = BIM.drop_na_rows(dfs)
        
        print('\n* Removing Total rows...')
        for key, df in dfs.items():
            df.dropna(axis=0, how='any', inplace=True)
        
        # filter items by 'Interior' function.
        if self.BIM_filter_out_interior_elements:
            print("\n* Filtering out elements with function: 'Interior'..." )
            dfs = BIM.filter_by_function(dfs, retain_col='Exterior')
        
        print('\n* Dealing with Windows...')
        dfs = BIM.deal_with_windows(dfs, keyword, mullion_width=self.BIM_window_mullion_width)
        
        print('\n* Dealing with Doors...')
        dfs = BIM.deal_with_doors(dfs, keyword=keyword, action=self.BIM_door_action)
    
        print('\n* Dealing with Curtain Walls...')
        dfs = BIM.deal_with_curtain_walls(dfs, keyword, action=self.BIM_curtain_wall_action)
    
        print('\n* Dealing with Curtain Panels...')
        dfs = BIM.deal_with_curtain_panels(dfs, keyword, action=self.BIM_curtain_panel_action, mullion_width = self.BIM_panel_mullion_width,
                                           family_filter_strs=self.BIM_family_filter_strs)
        
        print('\n* Processing BIM geometry...')
        BIMdf = BIM.Make_BIM_area_df_from_dfs(dfs)
        BIMdf = BIM.Remove_keyword_from_col_names(BIMdf, keyword=keyword)
        BIMdf = BIM.make_column_names_compatible(BIMdf)
        
        print('\n* Reconciling BIM and BEM geometric info...')
                
        Allkeys = ['BIM_Geo'] + [BEM[0] for BEM in self.BEMs]
        Alldfs = [BIMdf.sum().to_frame(name='BIM_Geo').T] + BEMdfs
        Alldf = pd.concat(Alldfs, axis=1, keys=Allkeys, sort=True)
        
        print('\n* Plotting...')
        Plotting.plot_geometry_comparison(Alldf, self.name, figpath=self.figpath, savefig=self.savefig)
        
        return Alldf
        
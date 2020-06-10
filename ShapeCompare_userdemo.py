# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 09:44:28 2020
@author: Seungyeon Hong
@script serves as part 2 of ShapeCompare toolkit
"""

import ShapeCompare.main as main

# mount a variable as ShapeCompare.main class
MyProject = main.Project()

# configure meta settings
MyProject.name('High Complexity Building (EVE Park)')
MyProject.keyword('_SY')
MyProject.savefig(False)
MyProject.figpath(r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\Scripts\Figures\dummy.png')

# add a BIM geometry
MyProject.BIM_add(r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\GeometryExport\BIM_EVE.xlsx') #an excel path

# add a BEM geometry (or BEM geometries)
MyProject.BEM_add('Approach1', r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\GeometryExport\Approach1_EVE.xlsx')# html path 1
MyProject.BEM_add('Approach2', r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\GeometryExport\Approach2_EVE_empty.xlsx')# excel or html path 2
MyProject.BEM_add('Approach3', r'C:\Users\temp\Documents\Carleton_GradStudies\Thesis\RevitModels\EUIcomparison\EVE\Approach3\EVE_Approach3_modTable.html') # excel or html path 3

# toggle options
MyProject.BIM_filter_out_interior_elements(False)
MyProject.BIM_window_mullion_width = 0.25
MyProject.BIM_door_action = 'lump_to_window' #options: 'remove', 'lump_to_window'
MyProject.BIM_family_filter_strs = ['Empty','Sloped'] # list of strings to filter out
MyProject.BIM_curtain_wall_action = 'remove' # options: 'remove', 'lump_to_wall', 'lump_to_window'
MyProject.BIM_curtain_panel_action = 'lump_to_wall' #options: 'remove', 'lump_to_wall', 'lump_to_window'
MyProject.BIM_panel_mullion_width = 0

# process information & produce plots
MyProject.execute()

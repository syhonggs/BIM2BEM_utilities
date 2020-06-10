# BIM2BEM_utilities
# 2020-06-10

This repository contains the ShapeCompare toolkit, born out of a master thesis work titled 'Geometric Accuracy of BIM-BEM
Transformation Workflows: Bridging the State-of-the-Art and Practice' by Seungyeon Hong.

BIM is becoming an increasingly common starting point to developing building energy models (BEMs) from. The existing BIM-BEM transformation workflows are problematic in that they do not offer any quality assurance - the user has no idea whether the resulting BEM is close to the original BIM or significant changes have been incurred during the transformation process. The toolkit contained in this repository is an effort to provide quality checking with regards to geometric accuracy of the BIM-BEM transformation process, by cross-checking the BIM geometry against a BEM geometry (or against multiple BEM geometries).

The toolkit is comprised of two parts: Revit-side code (in Dynamo) and Python code. Revit-side code creates wall, window, door, curtain panel, and space schedules to export onto an excel file. Python code then reads in the BIM geometry from the excel doc, as well as BEM geometry from html reports (or optionally from excel) produced after an EnergyPlus run.

Part0: Preparation
- download and unzip the repository into a preferred folder.

Part1: Revit-side code (Dynamo)
- Revit model's surfaces and volumes are to be compared against BEM geometry. Therefore Revit elements must represent correct physical functions (e.g. Roofs should not be modelled by Floor elements). Also, the portion of the objects that protrude outside of the building envelope (e.g. floor slabs extending outside the envelope to form balconies) must be split at the envelope boundary and be assigned correct functions (either Interior or Exterior).
- In Revit, go to Manage tab -> Visual Programming ribbon -> Dynamo Player.
- On the Dynamo Player pop-up, click Browse to Folder and navigate to the 'ShapeCompare_Dynamo' folder. Three scripts with individual 'play' buttons show up. 
- For each script, the calculator-like 'Edit inputs' button allows the user to edit the two inputs necessary to run the scripts. 'Keyword' variable is found in cripts 0, 1, 2, and it specifies the suffix to be appended to the custom schedules to prevent name clashes. Specify the same keyword across the three scripts, and also in the Python code later. Script 2 also requires an excel path to dump geometric information onto. Excel file does not need to exist, however the excel path must end with .xlsx extension.
- Click 'play' button on scripts 0, 1, 2 in sequence. A number of schedules will be created within Revit and then dumped onto an Excel file.

Part2: Python code
- If Python 3 is not installed, install it.
- Install all dependencies in one shot by using the command line interface. Using a virtual environment is recommended, though optional. Navigate to the correct directory and type $ pip install -r requirements.txt, or if you're using Anaconda distribution, then do $ conda install -r requirements.txt.
- The rest of operations in Python is shown as an example in the ShapeCompare_userdemo.py file. Care was taken to make it most user friendly within the user's capacity. It is perhaps the best to just copy the ShapeCompare_userdemo.py file and tweak the inputs. The comparison of BIM and BEM (or multiple BEMs) geometries are provided in four bar plots, each illustrating a building-level geometric proxy (exterior wall area, exterior window area, floor area, and volume). Images can be saved to a destination.

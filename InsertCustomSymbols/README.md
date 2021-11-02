# Insert Custom Symbols

This a set of Python scripts that custom symbols into a FreeCAD TechDraw Page.

## Installation

The installation is requires two steps.

***Step 1***

The directory where custom symbols are stored must be defined.

Place *set_dir_param.py* in the FreeCAD macro directory, typically in the Macro directory of your FreeCAD installation. (The location can be verified by selecting the Macro>Macros menu and looking at the macro location at the bottom of the Execute macro dialog.)

Run *set_dir_param.py* to select the directory where the symbol files are stored.

A dialog will be presented and the user can navigate to the directory. When the **Open** button is clicked the selected directory will be stored in the FreeCAD user parameters.

This file only needs to be run if the directory changes or the parameter is no longer present (possibly because of an update to FreeCAD, etc.)

***Step 2***

Place *Insert_Custom_Symbols.py* in the FreeCAD macro directory, typically in the Macro directory of your FreeCAD installation. (The location can be verified by selecting the Macro>Macros menu and looking at the macro location at the bottom of the Execute macro dialog.)

Also put a copy of the icon provided in the same directory.

This file can be run from the Macro menu in FreeCAD as any other macro or:

Follow the instructions in the following link to add a macro to the TechDraw toolbar.

## Usage

Select a TechDraw Page.

Execute the macro (Python) (either from the Macro menu or from the toolbar created above. The user will be presented with a dialog that allows the selection of a symbol from the directory defined in ***Installation Step 1***.

Select the desired symbol and click Open and the symbol will be added to the TechDraw page.


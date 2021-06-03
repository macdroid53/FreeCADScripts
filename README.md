# FreeCADScripts
A variety of Python scripts I've written for use with FreeCAD

## Arc Slot Utility
Arc Slot is to be used in an open sketch and will create a constrained, arced slot.
Optionally, it can be self constrained (that is it will move as a whole, with geometry and constraints) or
the same but constrained to a vertex selected bt the use before the executing the script.
The script displays a dialog where the user must enter the values of the slot radius and width.

## Rounded Rectangle Utility
Rounded Rectangle is to be used in an open sketch and will create a constrained, rectangle with rounded corners.
Optionally, it can be self constrained (that is it will move as a whole, with geometry and constraints) or
the same but constrained to a vertex selected bt the use before the executing the script.
The script displays a dialog where the user must enter the values of the rectangle height, witdh, and corner radius.

## Installation
Locate the local FreeCAD macros directory as described in the FreeCAD wiki:
[Macros directory](https://wiki.freecadweb.org/How_to_install_macros#Macros_directory "Macros directory")

Put copies of all files associated with the script (Python, images, etc.) from this repository.

There are typically two Python files with each utility. One contains the main code <utility name>.py, the other <utility name>ui.py contains any associated UI ( dialogs ).

The utility can be run from the FreeCAD Macro menu by selected and executing the <utility name>.py file

Once installed, the utilities can also be added to toolbars as described in the FreeCAD wiki:
[Customize Toolbars](https://wiki.freecadweb.org/Customize_Toolbars)

## Known issues:
* None
Various python scripts that can be imported into ArcGIS
as a python toolbox. NOTE - python toolboxes were introduced
in ArcGIS 10.1. You must create a python toolbox, not
your standard toolbox, for this to run.

**Pull Replica**

Simple tool to pull feature services from ArcGIS Online into a zipped
geodatabase, preserving domain values.
Provides the option to pull attachments or not (which is not provided in AGO when exporting a FS to a geodatabase).

Requires path to feature service, account login, and whether to
pull the attachments or not (defaults to no attachments).


**Get Attachments**
###### TODO
+ Handle OS functionality for overwriting
+ Look into optional field for naming
+ roll into python toolbox

~~~~~~


Interact with Feature Service to pull any photo attachments
stored in features. Builds a local directory as follows:


Photos -->
    [Feature Name] -->
        Attachment 1.jpg
        Attachment 2.jpg

Requires path to feature service, account login, and, optional,
an attribute field to name features.

~~~~~~
Please provide any feedback or improvements to the code.

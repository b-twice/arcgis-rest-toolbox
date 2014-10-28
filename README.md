Toolbox for working with the ArcGIS Rest Service for ArcGIS Online. Run restservices.py (compatible with Python 2.6+) from python or port restservices_toolbox over into a python toolbox (introduced in ArcGIS 10.1) and run from there.

Functionality includes:

**Pull Replica**

Simple tool to pull feature services from ArcGIS Online into a zipped
geodatabase, preserving domain values.
Provides the option to pull attachments or not (which is not provided in AGO when exporting a FS to a geodatabase).

Requires path to feature service, account login, and whether to
pull the attachments or not (defaults to no attachments).


**Get Attachments**
~~~~~~

Interact with Feature Service to pull any photo attachments
stored in features. Builds a local directory as follows:

Photos -->
    [Feature Name] -->
        Attachment 1.jpg
        Attachment 2.jpg

Requires path to feature service, account login, and, optional,
an attribute field to name features.

If the attribute field is empty, then defaults to globalid.

~~~~~~
Please provide any feedback or improvements to the code.

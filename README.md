## Rest Service Toolbox

Toolbox for working with the ArcGIS Rest Service for ArcGIS Online. Run restservices.py (compatible with Python 2.6+) from python or port restservices_toolbox over into a python toolbox (introduced in ArcGIS 10.1) and run from there.

Functionality includes:

### Pull Replica

Simple tool to pull feature services from ArcGIS Online into a zipped
geodatabase, preserving domain values.
Provides the option to pull attachments or not (which is not provided in AGO when exporting a FS to a geodatabase).

### Pull Attachments

Interact with Feature Service to pull any photo attachments
stored in features. Builds a local directory as follows:

Photos -->
    [Feature Name] -->
        Attachment 1.jpg
        Attachment 2.jpg

Requires path to feature service, account login, and, optional,
an attribute field to name features.

If the attribute field is empty then [Feature Name] will be labeled the corresponding record from the corresponding field, else [Feature Name] will be globalid.

### Update Service

Update records in a feature layer with changes in a CSV table. Useful for providing batch updates a field or fields in a feature layer without having to pull the feature service down and republish.

##### A Note on Attachments and Exif Metadata

All metadata is carried through no matter what method you use to pull down attachments, either through exporting to a geodatabase or pulling attachments with this tool.

However, if you are using one of Esri's mobile app, such as Collector or the "Green" App, and you are adding an attachment with a photo taken from within the app to a feature service with attachments enabled, no metadata will be added.

If you experience anything otherwise, notify and I will look into.

Please provide any feedback or improvements to the code.

## Rest Service Toolbox

Toolbox for working with ArcGIS's Rest Service in tandum with ArcGIS Online. Run restservices.py (compatible with Python 2.6 - 2.7) from python or port restservices_toolbox over into a python toolbox (introduced in ArcGIS 10.1) and run from there.

Functionality includes:

### Pull Replica

Simple tool to pull feature services from ArcGIS Online into a zipped
geodatabase, preserving domain values.

Provides the option to pull attachments or not.

**NOTE** - As of the latter half of 2014, this functionality is now implemented in the directory of a feature service. However, this tool can serve as a convenience function and as a saner method for dating and tracking your downloads.

Read more about how to do this over in the [API](http://services.arcgis.com/help/fsCreateReplica.html)

### Pull Attachments

Interact with a Feature Service to pull any photo attachments
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

### A Note on Attachments and Exif Metadata

All metadata is carried through no matter what method you use to pull down attachments, either through exporting to a geodatabase or pulling attachments with this tool.

However, if you are using one of Esri's mobile app, such as Collector or the "Green" App, and you are adding a photo taken from within the app to a feature service, no metadata will be added.

If you experience anything otherwise, notify me and I will look into.

Please provide any feedback or improvements to the code.

import json, urllib, urllib2, urlparse
import os, shutil
import time
import imghdr
import re
import csv
import arcpy

### REST FUNCTIONS

def check_service(service_url):
    url_parts = {"fs_url": None, "layer_url":None, "layer_id":None}
    components = os.path.split(service_url)
    if service_url == None:
        return True
    elif (components[1].isdigit() and os.path.split(components[0])[1] ==
    "FeatureServer"):
        url_parts["fs_url"] = components[0]
        url_parts["layer_url"] = service_url
        url_parts["layer_id"] = str(components[1])
        return url_parts
    elif components[1] == "FeatureServer":
        url_parts["fs_url"] = service_url
        return url_parts
    else:
        return False

def get_service_name(service_url):
    components = os.path.split(service_url)
    if components[1] == "FeatureServer":
        return os.path.split(components[0])[1]
    else:
        return get_service_name(components[0])

def get_response(url, query='', get_json=True):
    encoded = urllib.urlencode(query)
    request = urllib2.Request(url, encoded)
    if get_json:
        json_response = json.loads(urllib2.urlopen(request).read())
        if 'error' in json_response:
            print json_response
            exit()
        else:
            return json_response
    return urllib2.urlopen(request).read()

def add_path(url, *args):
    for arg in args:
        url = urlparse.urljoin(url + "/", str(arg))
    return url

def login (username, password):
    CREDENTIALS['username'] = username
    CREDENTIALS['password'] = password
    response = get_response(TOKEN_URL, CREDENTIALS)
    return response['token']

def get_service_info(input_url, token):
    return get_response(input_url,
        {'f':'json', 'token':token})

def query_id_or_field(url, query, field=None):
    if field:
        query['returnIdsOnly'] = 'false'
        query['outFields'] = field
        attributes= get_response(url, query)['features'][0]['attributes']
        if field in attributes:
            field_attribute = attributes[field]
            if field_attribute:
                return str(field_attribute)
    query['returnIdsOnly'] = 'true'
    return str(get_response(url, query)['objectIds'][0])

### OS FUNCTIONS

def create_and_set_dir(directory_name, optional_id=0):
    valid_directory = re.sub('[^\w\-_\. \(\)]', '_', directory_name)
    while os.path.exists(valid_directory):
        valid_directory = "{0} ({1})".format(directory_name, optional_id)
        optional_id += 1
    new_dir = os.path.join(os.getcwd(), valid_directory)
    os.makedirs(valid_directory)
    os.chdir(valid_directory)
    return new_dir

def pull_to_local(url, name, destination, file_format = ''):
    if destination:
        os.chdir(destination)
    if file_format:
        output = open('{0}.{1}'.format(name,file_format), 'wb')
    else:
        output = open(name, 'wb')
    output.write(url)
    output.close()

def group_photos(root_directory, new_directory):
    os.chdir(root_directory)
    photos = [(os.path.join(directory, filename), filename) for directory,
              dirnames, files in os.walk(root_directory) for filename in files if imghdr.what(os.path.join(directory,filename))]
    if len(photos) > 0:
        directory_path = create_and_set_dir(new_directory)
        for photo in photos:
            shutil.copy2(photo[0], os.path.join(directory_path, photo[1]))

def csv_to_json(data):
    update_array = []
    with open(data) as csv_data:
        for i,row in enumerate(csv.DictReader(csv_data)):
            update_array.append(dict(
                attributes = dict()))
            for key in row.keys():
                update_array[i]["attributes"][key] = row[key]
    return update_array


### QUERIES

CREDENTIALS = {
    'username': '',
    'password': '',
    'expiration': '300',
    'client': 'referer',
    'referer': 'www.arcgis.com',
    'f': 'json'
}

TOKEN_URL = "https://www.arcgis.com/sharing/rest/generateToken"

ATTACHMENTS = {
    'where': '1=1',
    'token': '',
    'f': 'json',
    'returnGeometry':'false'
}

REPLICA = {
    "geometry": '',
    "geometryType": "esriGeometryEnvelope",
    "inSR": '',
    "layerQueries": '',
    "layers": '0',
    "replicaName": "read_only_rep",
    "returnAttachments": 'false',
    "returnAttachmentsDataByUrl": 'true',
    "transportType": "esriTransportTypeEmbedded",
    "async": 'false',
    "syncModel": "none",
    "dataFormat": "filegdb",
    "token": '',
    "replicaOptions": '',
    "f": "json"
}

UPDATES = {
    "f": "json",
    "features": '',
    "rollbackOnFailure":True

}


class App(object):
    ''' Class with methods to perform tasks with ESRI's REST API '''
    def __init__ (self, input_url, token, destination):
        self.input_url = input_url
        self.token = token
        self.destination = destination
        self.layer_url = None
        self.layer_id = None
        self.fs_url = self.check_input_url()

    def check_input_url(self):
        url_parts = check_service(self.input_url)
        self.layer_url = url_parts["layer_url"]
        self.layer_id = url_parts["layer_id"]
        if not self.layer_url:
            self.layer_url = add_path(url_parts["fs_url"], "0")
        return url_parts["fs_url"]

    def get_root_name(self):
        return time.strftime("%Y_%m_%d_") + get_service_name(self.fs_url)

    def find_attachments(self, query, layer, field):
        root_file = create_and_set_dir(layer['name'])
        layer_query = add_path(self.fs_url, layer['id'], 'query')
        query['returnIdsOnly'] = 'true'
        feature_ids = get_response(layer_query, query)['objectIds']
        for feature in feature_ids:
                os.chdir(root_file)
                img_url = add_path(self.fs_url, layer['id'], feature,
                    'attachments')
                query['objectIds'] = feature
                attachments = get_response(img_url,query)['attachmentInfos']
                if len(attachments) > 0:
                    feature_name = query_id_or_field(layer_query, query, field)
                    create_and_set_dir(feature_name, feature)
                    for attachment in attachments:
                        attachment_url = add_path(img_url, attachment['id'],
                            'download')
                        try:
                            attachment_file = get_response(attachment_url,
                                {'token':self.token},
                                get_json = False)
                            pull_to_local(attachment_file, attachment['id'],
                                '', 'jpg')
                        except urllib2.HTTPError:
                            print "HTTP Error: {} could not be downloaded.".format(attachment_url)
        group_photos(root_file, "ALL")

    def pull_attachments(self, query, field):
        query['token'] = self.token
        os.chdir(self.destination)
        layers = get_service_info(self.fs_url, self.token)['layers']
        root_name = self.get_root_name() + "_Photos"
        if os.path.exists(root_name):
            shutil.rmtree(root_name)
        service_file = create_and_set_dir(root_name)
        attachments = get_service_info(self.layer_url,
            self.token)['hasAttachments']
        if self.layer_id and attachments:
            self.find_attachments(query, layers[int(self.layer_id)], field)
        else:
            for layer in layers:
                if get_service_info(add_path(self.fs_url, layer['id']),
                    self.token)['hasAttachments']:
                    os.chdir(service_file)
                    self.find_attachments(query, layer, field)

    def replicate(self, query):
        replica_url = add_path(self.fs_url, 'createReplica')
        zip_url = get_response(replica_url, query)['responseUrl']
        zip_file = get_response(zip_url, get_json=False)
        pull_to_local(zip_file, self.get_root_name(), self.destination, 'zip')


    def pull_replica(self, query):
        query['token'] = self.token
        layers = get_service_info(self.fs_url, self.token)['layers']
        if self.layer_id:
            query['layers'] = self.layer_id
            self.replicate(query)
        else:
            query['layers'] = [layer['id'] for layer in layers]
            self.replicate(query)

    def update_service(self, query, update_table):
        update_url = add_path(self.layer_url, 'updateFeatures')
        query["features"] = csv_to_json(update_table)
        query['token'] = self.token
        get_response(update_url, query)

class Toolbox(object):
    def __init__(self):
        self.label = "ArcGIS REST API Toolbox"
        self.alias = "Tools to interacte with the ArcGIS REST API"
        self.tools = [Replicate, PullAttachments, UpdateService]


class Replicate(object):
    def __init__(self):
        self.label = "Replicate Feature Service"
        self.description = ''' Pull a feature service from a feature service into a zipped geodatabase.'''
        self.canRunInBackground = True

    def getParameterInfo(self):
        in_service = arcpy.Parameter(
            displayName = 'Input Feature Service URL',
            name = 'in_service',
            datatype = 'GPString',
            parameterType = 'Required',
            direction = 'Input')

        in_username = arcpy.Parameter(
            displayName = 'Input Username to ArcGIS Online Account',
            name = 'in_username',
            datatype = 'GPString',
            parameterType = 'Required',
            direction = 'Input')

        in_password = arcpy.Parameter(
            displayName = 'Input Password to ArcGIS Online Account',
            name = 'in_password',
            datatype = 'GPString',
            parameterType = 'Required',
            direction = 'Input')

        out_directory = arcpy.Parameter(
            displayName = 'Output Directory',
            name = 'out_directory',
            datatype = 'DEFolder',
            parameterType = 'Required',
            direction = 'Input')

        has_attachments = arcpy.Parameter(
            displayName = 'Pull Attachments?',
            name = 'has_attachments',
            datatype = 'GPBoolean',
            parameterType = 'Required',
            direction = 'Input')

        out_directory.filter.list = ['File System']
        has_attachments.value = False
        params = [in_service, in_username, in_password, out_directory, has_attachments]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        in_service = parameters[0].valueAsText
        in_username = parameters[1].valueAsText
        in_password = parameters[2].valueAsText
        out_directory = parameters[3].valueAsText
        has_attachments = parameters[4].valueAsText

        try:
            token = login(in_username, in_password)
            if 'error' in token:
                raise KeyError('token')
            REPLICA['returnAttachments'] = has_attachments
            run = App(in_service, token, out_directory)
            run.pull_replica(REPLICA)

        except KeyError as e:
            if e.message == 'token':
                messages.addErrorMessage('The token cannot be obtained, check your credentials.')
        except ValueError:
            messages.addErrorMessage('Check your feature service url again. {0} is not working.'.format(in_service))

class PullAttachments(object):
    def __init__(self):
        self.label = "Pull Attachments"
        self.description = ''' Pull attachments from a feature service into a local directory.'''
        self.canRunInBackground = True

    def getParameterInfo(self):
        in_service = arcpy.Parameter(
            displayName = 'Input Feature Service URL',
            name = 'in_service',
            datatype = 'GPString',
            parameterType = 'Required',
            direction = 'Input')

        in_username = arcpy.Parameter(
            displayName = 'Input Username to ArcGIS Online Account',
            name = 'in_username',
            datatype = 'GPString',
            parameterType = 'Required',
            direction = 'Input')

        in_password = arcpy.Parameter(
            displayName = 'Input Password to ArcGIS Online Account',
            name = 'in_password',
            datatype = 'GPString',
            parameterType = 'Required',
            direction = 'Input')

        out_directory = arcpy.Parameter(
            displayName = 'Output Directory',
            name = 'out_directory',
            datatype = 'DEFolder',
            parameterType = 'Required',
            direction = 'Input')

        in_field = arcpy.Parameter(
            displayName = 'Field Name to label directories',
            name = 'in_field',
            datatype = 'GPString',
            parameterType = 'Optional',
            direction = 'Input')

        out_directory.filter.list = ['File System']
        params = [in_service, in_username, in_password, out_directory, in_field]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        in_service = parameters[0].valueAsText
        in_username = parameters[1].valueAsText
        in_password = parameters[2].valueAsText
        out_directory = parameters[3].valueAsText
        in_field = parameters[4].valueAsText

        try:
            token = login(in_username, in_password)
            if 'error' in token:
                raise KeyError('token')
            run = App(in_service, token, out_directory)
            run.pull_attachments(ATTACHMENTS, in_field)

        except KeyError as e:
            if e.message == 'token':
                messages.addErrorMessage('The token cannot be obtained, check your credentials.')
        except ValueError:
            messages.addErrorMessage('Check your feature service url again. {0} is not working.'.format(in_service))

        except urllib2.HTTPError as e:
            if e.message == 'httperror':
                messages.addMessage('The attachment could not be downloaded')

class UpdateService(object):
    def __init__(self):
        self.label = "Update Service"
        self.description = ''' Update records in a Feature Service.'''
        self.canRunInBackground = True

    def getParameterInfo(self):
        in_service = arcpy.Parameter(
            displayName = 'Input Feature Service URL',
            name = 'in_service',
            datatype = 'GPString',
            parameterType = 'Required',
            direction = 'Input')

        in_username = arcpy.Parameter(
            displayName = 'Input Username to ArcGIS Online Account',
            name = 'in_username',
            datatype = 'GPString',
            parameterType = 'Required',
            direction = 'Input')

        in_password = arcpy.Parameter(
            displayName = 'Input Password to ArcGIS Online Account',
            name = 'in_password',
            datatype = 'GPString',
            parameterType = 'Required',
            direction = 'Input')

        in_csv = arcpy.Parameter(
            displayName = 'Input CSV of records to update',
            name = 'in_csv',
            datatype = 'DEFile',
            parameterType = 'Required',
            direction = 'Input')

        params = [
            in_service,
            in_username,
            in_password,
            in_csv]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        in_service = parameters[0].valueAsText
        in_username = parameters[1].valueAsText
        in_password = parameters[2].valueAsText
        in_csv = parameters[3].valueAsText

        try:
            token = login(in_username, in_password)
            if 'error' in token:
                raise KeyError('token')
            run = App(in_service, token, "")
            run.update_service(UPDATES, in_csv)

        except KeyError as e:
            if e.message == 'token':
                messages.addErrorMessage('The token cannot be obtained, check your credentials.')
        except ValueError:
            messages.addErrorMessage('Check your feature service url again. {0} is not working.'.format(in_service))

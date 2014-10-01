import arcpy
import os
import json, urllib, urllib2
import urlparse
import time

CREDENTIALS = {
    'username': '',
    'password': '',
    'expiration': '60',
    'client': 'referer',
    'referer': 'www.arcgis.com',
    'f': 'json'
}

TOKEN_URL = "https://www.arcgis.com/sharing/rest/generateToken"

REPLICA = {
    "geometry": '',
    "geometryType": "esriGeometryEnvelope",
    "inSR": '',
    "layerQueries": '',
    "layers": "0",
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


def get_response(url, query='', get_json=True):
    encoded = urllib.urlencode(query)
    request = urllib2.Request(url, encoded)
    if get_json:
        return json.loads(urllib2.urlopen(request).read())
    return urllib2.urlopen(request).read()

def add_path(url, path):
    return urlparse.urljoin(url + "/", path)

def login (username, password):
    CREDENTIALS['username'] = username
    CREDENTIALS['password'] = password
    response = get_response(TOKEN_URL, CREDENTIALS)
    if 'error' in response:
        return response
    else:
        return response['token']

def get_fs_name(input_url, token):
    return get_response(input_url,
        {'f':'json', 'token':token})['layers']

### OS functions

def create_and_set_dir(directory_name):
    new_dir = os.path.join(os.getcwd(), directory_name)
    os.makedirs(directory_name)
    os.chdir(directory_name)
    return new_dir

def pull_to_local(url, name, destination, file_format = ''):
    if destination:
        os.chdir(destination)
    if format:
        output = open(str(name) + '.{}'.format(file_format), 'wb')
    else:
        output = open(str(name), 'wb')
    output.write(url)
    output.close()

class App(object):
    ''' Class with methods to perform tasks with ESRI's REST service '''
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

    def replicate(self, query, layer):
        replica_url = add_path(self.fs_url, 'createReplica')
        zip_url = get_response(replica_url, query)['responseUrl']
        zip_file = get_response(zip_url, get_json=False)
        file_name = time.strftime("%Y_%m_%d_") + layer['name']
        pull_to_local(zip_file, file_name, self.destination, 'zip')


    def pull_replica(self, query):
        query['token'] = self.token
        layers = get_fs_name(self.fs_url, self.token)
        if self.layer_id:
            query['layers'] = self.layer_id
            self.replicate(query, layers[int(self.layer_id)])
        else:
            for layer in layers:
                query['layers'] = layer['id']
                self.replicate(query, layer)

class Toolbox(object):
    def __init__(self):
        self.label = "Replicate Feature Service"
        self.alias = "Replicate Feature Service"
        self.tools = [PullReplica]


class PullReplica(object):
    def __init__(self):
        self.label = "Replicate"
        self.description = ''' Pull a feature service from ArcGIS Online
                           into a zipped geodatabase.'''
        self.canRunInBackground = True

    def getParameterInfo(self):
        in_service = arcpy.Parameter(
            displayName = 'Input Feature Service URL',
            name = 'in_service',
            datatype = 'String',
            parameterType = 'Required',
            direction = 'Input')

        in_username = arcpy.Parameter(
            displayName = 'Input Username to ArcGIS Online Account',
            name = 'in_username',
            datatype = 'String',
            parameterType = 'Required',
            direction = 'Input')

        in_password = arcpy.Parameter(
            displayName = 'Input Password to ArcGIS Online Account',
            name = 'in_password',
            datatype = 'String',
            parameterType = 'Required',
            direction = 'Input')

        out_directory = arcpy.Parameter(
            displayName = 'Output Directory',
            name = 'out_directory',
            datatype = 'String',
            parameterType = 'Required',
            direction = 'Input')

        has_attachments = arcpy.Parameter(
            displayName = 'Pull Attachments?',
            name = 'has_attachments',
            datatype = 'Boolean',
            parameterType = 'Required',
            direction = 'Input')

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
            messages.addErrorMessage('Check your feature service url again. {} is not working.'.format(in_service))


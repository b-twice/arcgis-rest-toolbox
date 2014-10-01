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
    if service_url == None:
        return True
    else:
        if os.path.split(service_url)[-1] != "FeatureServer":
            return False
        return True

def get_response(url, query='', return_json=True):
    encoded_query = urllib.urlencode(query)
    request = urllib2.Request(url, encoded_query)
    if return_json:
        return json.loads(urllib2.urlopen(request).read())
    return urllib2.urlopen(request).read()

def add_path(url, path):
    return urlparse.urljoin(url + "/", path)

def pull_to_local(url, name, destination, file_format = ''):
    if destination:
        os.chdir(destination)
    if format:
        output = open(str(name) + '.{}'.format(file_format), 'wb')
    else:
        output = open(str(name), 'wb')
    output.write(url)
    output.close()

def login (username, password):
    CREDENTIALS['username'] = username
    CREDENTIALS['password'] = password
    response = get_response(TOKEN_URL, CREDENTIALS)
    if 'error' in response:
        print response['error']
        exit()
    else:
        return response['token']

def get_fs_name(input_url, token):
    return get_response(input_url,
        {'f':'json', 'token':token})['layers'][0]['name']

def pull_replica(fs_url, query, token, destination):
    query['token'] = token
    replica_url = add_path(fs_url, "createReplica")
    zip_url = get_response(replica_url, query)['responseUrl']
    zip_file = get_response(zip_url, return_json=False)
    file_name = time.strftime("%Y_%m_%d_") + get_fs_name(fs_url, token)
    pull_to_local(zip_file, file_name, destination, 'zip')


class Toolbox(object):
     def __init__(self):
          self.label = "Create a Replica from a Feature Service"
          self.alias = "feature service"
          self.tools = [PullReplica]


class PullReplica(object):
     def __init__(self):
          self.label = "Replicate Feature Service"
          self.description = ''' Pull a feature service from ArcGIS Online
                               into a zipped geodatabase. This preserves all
                               domains and provides option forattachments.'''
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
            parameterType = 'REquired',
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
          if not check_service(parameters[0].value):
               parameters[0].setErrorMessage("Service URL must end with 'FeatureServer'")
          return

     def execute(self, parameters, messages):

          in_service = parameters[0].valueAsText
          in_username = parameters[1].valueAsText
          in_password = parameters[2].valueAsText
          out_directory = parameters[3].valueAsText
          has_attachments = parameters[4].valueAsText

          try:
               token = login(in_username, in_password)
               REPLICA['returnAttachments'] = has_attachments
               pull_replica(in_service, REPLICA, token, out_directory)

          except KeyError as e:
               if e.message == 'token':
                    messages.addErrorMessage('The token cannot be obtained, check your credentials.')
          except ValueError:
               messages.addErrorMessage('Check your feature service url again. {} is not working.'.format(in_service))

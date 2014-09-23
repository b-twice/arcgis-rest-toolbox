import arcpy
import os
import json, urllib, urllib2
import urlparse
import time

def checkService(service_url):
     if service_url == None:
          return True
     else:
          if os.path.split(service_url)[-1] != "FeatureServer":
               return False
          return True

def getResponse(url, query='', return_json=True):
     encoded_query = urllib.urlencode(query)
     request = urllib2.Request(url, encoded_query)
     if return_json:
          return json.loads(urllib2.urlopen(request).read())
     return urllib2.urlopen(request).read()

def addPath(url, path):
     return urlparse.urljoin(url + "/", path)

def pullToZip(url, name, destination):
     os.chdir(destination)
     output = open(name + ".zip", 'wb')
     output.write(url)
     output.close()

def genToken (username, password, referer='www.arcgis.com', expiration=60):
     '''Authorize user information with ArcGIS.com and obtain a token.'''
     query_dict = {'username': username,
                    'password': password,
                    'expiration': str(expiration),
                    'client': 'referer',
                    'referer': referer,
                    'f': 'json'}
     token_url = "https://www.arcgis.com/sharing/rest/generateToken"
     token = getResponse(token_url, query_dict)
     return token['token']

def createReplica (service_url, query, destination):
     ''' Makes three request to the Feature Service:
               1. One to "createReplica" to get url of the zip file
               2. One to zip url to get the zip file
               3. One to "featureServer" to get the layer name '''

     replica_url = addPath(service_url, "createReplica")
     zip_url = getResponse(replica_url, query)['responseUrl']
     zip_file = getResponse(zip_url, return_json=False)

     fs_resp =  getResponse(service_url, {'f':'json','token':query['token']})['layers'][0]['name']
     fs_name = time.strftime("%Y_%m_%d_") + fs_resp

     pullToZip(zip_file, fs_name, destination)
     arcpy.AddMessage("{} successfully replicated.".format(fs_name))

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
          if not checkService(parameters[0].value):
               parameters[0].setErrorMessage("Service does not end in 'FeatureService")
          return

     def execute(self, parameters, messages):

          replicaQuery = {"geometry": '',
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
               "f": "json"}

          inService = parameters[0].valueAsText
          inUsername = parameters[1].valueAsText
          inPassword = parameters[2].valueAsText
          outDirectory = parameters[3].valueAsText
          hasAttachments = parameters[4].valueAsText

          try:
               token = genToken(inUsername, inPassword)
               replicaQuery['token'] = token
               replicaQuery['returnAttachments'] = hasAttachments
               createReplica(inService, replicaQuery, outDirectory)

          except KeyError as e:
               if e.message == 'token':
                    messages.addErrorMessage('The token cannot be obtained, check your credentials.')
          except ValueError:
               messages.addErrorMessage('Check your feature service url again. {} is not working.'.format(inService))

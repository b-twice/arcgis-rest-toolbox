import json, urllib, urllib2
import sys, os
import arcpy
import shutil

class GetToken(object):
    '''A token must be generated and added to each query of the server for session verification'''

    def gentoken(self, username, password,
                referer = 'www.arcgis.com', expiration=60):
        '''Gets token from referer'''
        query_dict = {'username': username,
                      'password': password,
                      'expiration': str(expiration),
                      'client': 'referer',
                      'referer': referer,
                      'f': 'json'}
        query_string = urllib.urlencode(query_dict)
        token_url = "https://www.arcgis.com/sharing/rest/generateToken"
        token_response = urllib.urlopen(token_url, query_string)
        token = json.loads(token_response.read())
        return token['token']

class DownloadAttachments(GetToken):

    def __init__(self, fs, field, destination, username, password):
        self.fs = fs +'/'
        self.field = field
        self.where = '1=1'
        self.token = self.gentoken(username, password)
        self.destination = os.path.join(destination, 'Photos')

    def jsonload(self, url, query):
        '''Loads feature service with query and returns jso'''
        return json.loads(urllib.urlopen(url + query).read())

    def queryid(self):
        '''Query IDs and return list of object IDs'''
        objquery = ('query?where={}&returnIdsOnly=true&'
                    'f=json&token={}').format(self.where, self.token)
        return self.jsonload(self.fs, objquery)['objectIds']

    def queryfield(self):
        '''Query attributes based on field passed'''
        fieldquery = ('query?where={}&outFields={}&'
                'f=json&token={}').format(self.where,self.field, self.token)
        fieldtext = self.jsonload(self.fs,fieldquery)['features']
        return [str(f['attributes'][self.field]) for f in fieldtext]

    def zipdata(self):
        '''Id photos based on field query, if not, photo ids will be given a plain integer value'''
        id = self.queryid()
        try:
            if len(self.field) > 0:
                field = self.queryfield()
                return zip(id, field)
        except:
            return zip(id, map(id.count, id))

    def slashclean(self, path):
        '''REST service only accepts paths with forward slash'''
        return path.replace('\\','/')

    def queryimage(self, objectid):
        '''Each image has an id which can only be obtained via object id'''
        attachment = self.slashclean(os.path.join(
                                self.fs, str(objectid), 'attachments'))
        imgquery = ('?f=json&token={}'.format(self.token))
        imgreturn = self.jsonload(attachment, imgquery)['attachmentInfos']
        return [(objectid, img['id']) for img in imgreturn]

    def mapdict(self):
        '''Maps field name and photographs to dictionary with each
        object id as the key'''
        keys = self.zipdata()
        fsmap = {i[0]:{'name':i[1], 'photographs':[]} for i in keys}
        for key in keys:
            for img in self.queryimage(key[0]):
                fsmap[img[0]]['photographs'].append(img[1])
        return fsmap

    def downloadimage(self, imgid, imgurl):
        '''Takes url for image and downloads to directory'''
        req = urllib2.Request(imgurl)
        response = urllib2.urlopen(req)
        output = open(str(imgid) + '.jpg', 'wb')
        output.write(response.read())
        output.close()

    def allimages (self):
        photolist = [[os.path.join(dirpath, f),f] for dirpath, dirnames, files
            in os.walk(self.destination) for f in files if f.endswith('.jpg') or f.endswith('.jpg')]
        placement = os.path.join(self.destination, 'All Photos')
        os.makedirs(placement)
        for photo in photolist:
            shutil.copy(photo[0], placement)

    def pullimages(self):
        '''Creates a directory called photos and stores images attached
        to each feature in a subdirectory labelled by the field name
        given for the feature'''
        os.makedirs(self.destination)
        os.chdir(self.destination)
        for k, val in self.mapdict().iteritems():
            objfolder = os.path.join(self.destination, 'Feature ' + str(k))
            try:
                if val['name'] != 'None':
                    objfolder += ' ' + val['name']
            except:
                pass
            if not len(val['photographs']):
                objfolder += ' NO ATTACHMENTS'
            os.makedirs(objfolder)
            for imgid in val['photographs']:
                os.chdir(objfolder)
                imgurl = self.slashclean(os.path.join(
                    self.fs,str(k),'attachments',
                    str(imgid), 'download?token={}'.format(self.token)))
                self.downloadimage(imgid, imgurl)
        self.allimages()


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Download Attachments toolbox"
        self.alias = "attachments"

        # List of tool classes associated with this toolbox
        self.tools = [GetImages]


class GetImages(DownloadAttachments):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Download Attachments"
        self.description = ''' Download attachments takes a feature
                               service and pulls all photos from the service
                               into a directory organized with distinct
                               folders for each feature '''
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
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

        in_directory = arcpy.Parameter(
            displayName = 'Input workspace',
            name = 'in_directory',
            datatype = 'DEWorkspace',
            parameterType = 'Required',
            direction = 'Input')

        fields = arcpy.Parameter(
            displayName = 'Input Fields',
            name = 'in_fields',
            datatype = 'GPString',
            parameterType = 'Optional',
            direction = 'Input')

        in_directory.filter.list = ['File System']
        params = [in_service, in_username, in_password,in_directory, fields]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        inService = parameters[0].valueAsText
        inUsername = parameters[1].valueAsText
        inPassword = parameters[2].valueAsText
        inDirectory = parameters[3].valueAsText
        inFields = parameters[4].valueAsText
        try:
            run = DownloadAttachments(inService, inFields, inDirectory,
                                    inUsername, inPassword)
            run.pullimages()
        except WindowsError:
            messages.addErrorMessage('The directory \"Photos\" cannot be created within the location, {}, you gave. Please clear or change directories and try again.'.format(inDirectory))
        except KeyError as e:
            if e.message == 'token':
                messages.addErrorMessage('The token cannot be obtained...check your credentials.')
            else:
                messages.addErrorMessage('Oh my, it appears as if the feature service has no attachments.')
        except ValueError:
            messages.addErrorMessage('You might want to check your feature service url again. {} is not working.'.format(inService))


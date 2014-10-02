import json, urllib, urllib2, urlparse
import os, shutil
import time
import imghdr


### REST functions

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
        get_service_name(components[0])

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
        print response['error']
        exit()
    else:
        return response['token']

def get_layers(input_url, token):
    return get_response(input_url,
        {'f':'json', 'token':token})['layers']

def query_id_or_field(url, query, field=None):
    if field:
        query['outFields'] = field
        return get_response(url, query)['features']
    query['returnIdsOnly'] = 'true'
    return get_response(url, query)['objectIds']

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

def group_photos(root_directory, new_directory):
    os.chdir(root_directory)
    photos = [(os.path.join(directory, filename), filename) for directory,
              dirnames, files in os.walk(root_directory) for filename in files if imghdr.what(os.path.join(directory,filename))]
    directory_path = create_and_set_dir(new_directory)
    for photo in photos:
        shutil.copy2(photo[0], os.path.join(directory_path, photo[1]))

### Queries

CREDENTIALS = {
    'username': '',
    'password': '',
    'expiration': '60',
    'client': 'referer',
    'referer': 'www.arcgis.com',
    'f': 'json'
}

TOKEN_URL = "https://www.arcgis.com/sharing/rest/generateToken"

ATTACHMENTS = {
    'where': '1=1',
    'token': '',
    'f': 'json'
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

    def find_attachments(self, query, layer):
        root_name = time.strftime("%Y_%m_%d_") + layer['name'] + "_Photos"
        root_file = create_and_set_dir(root_name)
        layer_query = add_path(self.fs_url, "{}/query".format(layer['id']))
        feature_ids = query_id_or_field(layer_query, query)
        for feature in feature_ids:
            os.chdir(root_file)
            img_url = add_path(self.input_url,
                "{}/{}/attachments").format(layer['id'], feature)
            attachments = get_response(img_url, query)['attachmentInfos']
            if len(attachments) > 0:
                create_and_set_dir(str(feature))
                for attachment in attachments:
                    attachment_url = add_path(img_url,
                        "{}/download".format(attachment['id']))
                    attachment_file = get_response(attachment_url,
                        {'token':self.token},
                        get_json = False)
                    pull_to_local(attachment_file, attachment['id'],
                        '', 'jpg')
        group_photos(root_file, "ALL")

    def pull_attachments(self, query):
        query['token'] = self.token
        os.chdir(self.destination)
        layers = get_layers(self.fs_url, self.token)
        if self.layer_id:
            self.find_attachments(query, layers[self.layer_id])
        else:
            service_name = get_service_name(self.fs_url)
            create_and_set_dir(service_name)
            for layer in layers:
                os.chdir(service_name)
                self.find_attachments(query, layer)

    def replicate(self, query, layer):
        replica_url = add_path(self.fs_url, 'createReplica')
        zip_url = get_response(replica_url, query)['responseUrl']
        zip_file = get_response(zip_url, get_json=False)
        file_name = time.strftime("%Y_%m_%d_") + layer['name']
        pull_to_local(zip_file, file_name, self.destination, 'zip')


    def pull_replica(self, query):
        query['token'] = self.token
        layers = get_layers(self.fs_url, self.token)
        if self.layer_id:
            query['layers'] = self.layer_id
            self.replicate(query, layers[int(self.layer_id)])
        else:
            for layer in layers:
                query['layers'] = layer['id']
                self.replicate(query, layer)


if __name__ == "__main__":
    TOKEN = login("", "")
    INPUT_URL = ""
    DEST = r""
    RUN = App(INPUT_URL, TOKEN, DEST)
    #RUN.pull_replica(REPLICA)
    # pull attachments not reworked yet for new logic
    RUN.pull_attachments(ATTACHMENTS)


import json, urllib, urllib2, urlparse
import os, shutil
import time
import imghdr


### REST functions

def check_service(serviceUrl):
    if serviceUrl == None:
        return True
    else:
        if os.path.split(serviceUrl)[-1] != 'FeatureServer':
            return False
        return True

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

def get_fs_name(fs_url, token):
    return get_response(fs_url,
        {'f':'json', 'token':token})['layers'][0]['name']

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

def pull_replica(fs_url, query, token, destination):
    query['token'] = token
    replica_url = add_path(fs_url, "createReplica")
    zip_url = get_response(replica_url, query)['responseUrl']
    zip_file = get_response(zip_url, get_json=False)
    file_name = time.strftime("%Y_%m_%d_") + get_fs_name(fs_url, token)
    pull_to_local(zip_file, file_name, destination, 'zip')

if __name__ == "__main__":
    TOKEN = login("", "")
    FS_URL = ""
    DEST = r""
    pull_replica(FS_URL, REPLICA, TOKEN, DEST)


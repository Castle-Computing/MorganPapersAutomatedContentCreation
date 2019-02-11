import requests
from ConfigParser import RawConfigParser
from requests_toolbelt.multipart.encoder import MultipartEncoder

def authenticate():
    parser = RawConfigParser()
    parser.read('configuration.ini')

    m = MultipartEncoder(
        fields={'name': parser.get('DEFAULT', 'username'), 'pass': parser.get('DEFAULT', 'password'), 'op': 'Log in', 'form_id': 'user_login'}
    )

    session = requests.session()
    response = session.post('https://digital.lib.calpoly.edu/user/login', data=m, headers={'Content-Type': m.content_type})
    print("Authentication response code: " + str(response.status_code))
    return session

def deleteAndReUpload(session, pid, dsid, content):
    print("\nDeleting and uploading content for " + pid + ":")
    base_url = 'https://digital.lib.calpoly.edu/islandora/rest/v1/object/' + pid + '/datastream'
    delete_url = base_url + "/" + dsid

    delete_response = session.delete(delete_url)
    print("Deleting with " + delete_url + " returned code: " + str(delete_response.status_code))
    
    multipartFormData = MultipartEncoder(
        fields={
            'file': (dsid + ".txt", content, 'text/plain'),
            'dsid': dsid, 
            'controlGroup': 'M'
        }
    )

    headers = { 'Content-Type': multipartFormData.content_type }

    post_response = session.post(base_url, headers=headers, data=multipartFormData)
    print("Posting with " + base_url + " returned code: " + str(post_response.status_code))


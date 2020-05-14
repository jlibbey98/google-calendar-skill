import os.path
import httplib2

from apiclient import discovery

import oauth2client
from oauth2client import client
from oauth2client import file
from oauth2client import tools

CREDENTIAL_SECRET = '/home/pi/custom-dep/credentials_nd.json'
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'

def get_credentials():

    flags = None #'--noauth_local_webserver'
    credential_dir = os.path.expanduser('/home/pi/custom-dep')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'calendar_nd.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()

    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CREDENTIAL_SECRET, SCOPES)
        flow.user_agent = 'googcal.py'

        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:
            credentials = tools.run_flow(flow, store)

        print('Storing credentials to ' + credential_path)

    http = credentials.authorize(httplib2.Http())

    return discovery.build('calendar', 'v3', http=http)

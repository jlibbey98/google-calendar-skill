#   Copyright 2020 James Libbey
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os.path
import httplib2
import json

from apiclient import discovery

import oauth2client
from oauth2client import client
from oauth2client import file
from oauth2client import tools


CREDENTIAL_SECRET = 'google_calendar_skill_secret.json'
CREDENTIAL_TOKEN = 'google_calendar_skill_token.json'
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
API_ENABLE_URL = 'https://developers.google.com/calendar/quickstart/python'


def main():

    flags = None 

    # ensure that the credential directory exists when setting up
    credential_dir = os.path.expanduser('~/.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
        print('Created directory ' + credential_dir)
    token_path = os.path.join(credential_dir, CREDENTIAL_TOKEN)
    secret_path = os.path.join(credential_dir, CREDENTIAL_SECRET)

    # ensure that the token file exists when opening it
    with open(token_path, 'w') as f:
        f.close()
    print('Allocating ' + token_path + ' for Google Calendar Skill token file.')
    print(secret_path + ' will be allocated for Google Calendar Skill client secret file.\n')
    

    store = oauth2client.file.Storage(token_path)
    credentials = store.get()
    print('Opened Google Calendar Skill token file; follow these steps to set up credentials.')

    print('Visit the following URL:')
    print('\n\t' + API_ENABLE_URL + '\n')
    print('Click the blue \"Enable the Google Calendar API\" button. Then, click \"Create\" and the blue \"DOWNLOAD CLIENT CONFIGURATION\" button.')
    secret_json = json.loads(input('Copy the contents of the .json file here: '))

    # Write the input .json object to the secret file
    with open(secret_path, 'w') as outfile:
        json.dump(secret_json, outfile) 
        outfile.close()
    print('Wrote client secret to ' + secret_path)
        
    flow = client.flow_from_clientsecrets(secret_path, SCOPES)
    flow.user_agent = 'googcal.py'

    if flags:
        credentials = tools.run_flow(flow, store, flags)
    else:
        credentials = tools.run_flow(flow, store)

    print('Storing credentials to ' + token_path)

    

if __name__ == '__main__':
    main()

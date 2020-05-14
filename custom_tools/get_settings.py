import oauth2client

def get_settings(creds):

    settings = creds.settings().list().execute()

    for setting in settings['items']:
        if setting.get('id') == 'timezone':
            print(setting.get('value'))


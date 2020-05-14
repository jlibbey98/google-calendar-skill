from mycroft import MycroftSkill, intent_file_handler

import os.path
import datetime
import pytz
import httplib2
from apiclient import discovery

import oauth2client
from oauth2client import client
from oauth2client import file
from oauth2client import tools



class GoogleCalendar(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.dep_dir = '/home/pi/custom-dep'
        if not os.path.exists(self.dep_dir):
            os.makedirs(self.dep_dir)

        self.creds = None
        self.timezone = None

    def initialize(self):
        self.update_credentials()
        self.update_timezone()

    @intent_file_handler('calendar.google.intent')
    def handle_calendar_google(self, message):
        self.speak_dialog('let.me.check')

        events = self.get_events()
        if not events:
            self.speak_dialog('no.events.today')
        else:
            self.speak_dialog('today.you.have')
        
        for event in events:
            start_full = event['start'].get('dateTime', event['start'].get('date'))
            start_abbr = start_full[11:16]

            if start_abbr[3:] == '00':
                self.speak_dialog('event.is.at.hundred', {"event_summary": 
                        event['summary'], "event_time_start": start_abbr})
            else:
                self.speak_dialog('event.is.at', {"event_summary": event['summary'],
                    "event_time_start": start_abbr})


    def update_credentials(self):
        """
        Acquires the credentials for the Google Calendar and returns
        them after authorization and building
        """
      
        credential_path = os.path.join(self.dep_dir, 'calendar_nd.json')

        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()

        http = credentials.authorize(httplib2.Http())

        self.creds =  discovery.build('calendar', 'v3', http=http)


    def update_timezone(self):

        settings = self.creds.settings().list().execute()

        for setting in settings['items']:
            if setting.get('id') == 'timezone':
                self.timezone = pytz.timezone(setting.get('value'))
                return
        

    def get_events(self):
        """
        Accesses a list of the events over the course of the day and returns
        them in the following format:
        """

        now_dt = datetime.datetime.now(self.timezone)
        day_end_dt = now_dt.replace(hour=23, minute=59, second=59)

        now_str = now_dt.isoformat()
        day_end_str = day_end_dt.isoformat()

#        calendar_list = ['primary', 'Duncan Hall'] 
        """ 
        event_list = []
        for calendar in calendar_list:
            self.log.info(calendar)
            event_list.append(self.creds.events().list(calendarId=calendar,
                timeMin=now_str, timeMax=day_end_str, singleEvents=True,
                orderBy='startTime').execute())
        """
        event_list = self.creds.events().list(calendarId='primary',
                timeMin=now_str, timeMax=day_end_str, singleEvents=True,
                orderBy='startTime').execute()

        return event_list.get('items', [])




def create_skill():
    return GoogleCalendar()


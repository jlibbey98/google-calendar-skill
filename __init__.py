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

CREDENTIAL_TOKEN = 'google_calendar_skill_token.json'


class GoogleCalendar(MycroftSkill):

    def __init__(self):
        MycroftSkill.__init__(self)

        self.service = None
        self.timezone = None
        self.enabled_calendars = []

    def initialize(self):
        self.update_credentials()
        self.update_timezone()
        self.update_enabled_calendars()

    @intent_file_handler('calendar.google.intent')
    def handle_calendar_google(self, message):
        self.speak_dialog('let.me.check')

        event_list = self.get_events()

        if event_list:
            self.speak_dialog('today.you.have')
            if self.settings.get('en_24h_clock'):
                self.speak_24h(event_list)
            else:
                self.speak_12h(event_list)                            
        else:
            self.speak_dialog('no.events.today')


    def update_credentials(self):
        """
        Acquires the credentials for the Google Calendar and uses them to
        build the service; meant to be executed during initialization
        """
        
        # Obtain credentials
        credential_dir = os.path.expanduser('~/.credentials')
        credential_path = os.path.join(credential_dir, CREDENTIAL_TOKEN)
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()

        # If credentials are invalid, return error and notify user
        if not credentials or credentials.invalid or credentials == None:
            self.speak_dialog('credentials.invalid')
            self.log.error('Google Calendar Skill Error: Invalid credentials; run get_credentials.py in the skill directory to refresh.')

        # Authorize and build service from the credentials
        http = credentials.authorize(httplib2.Http())
        self.service =  discovery.build('calendar', 'v3', http=http)


    def update_timezone(self):

        settings = self.service.settings().list().execute()

        for setting in settings['items']:
            if setting.get('id') == 'timezone':
                self.timezone = pytz.timezone(setting.get('value'))
                return

    def update_enabled_calendars(self):

        self.enabled_calendars = self.settings.get('enabled_calendar_list').split(', ')
        

    def get_events(self):
        """
        Accesses a list of the events over the course of the day and returns
        them in the following format:
        """

        now_dt = datetime.datetime.now(self.timezone)
        day_end_dt = now_dt.replace(hour=23, minute=59, second=59)

        now_str = now_dt.isoformat()
        day_end_str = day_end_dt.isoformat()


        calendar_list = self.service.calendarList().list().execute()
        calendar_id_list = []
        # if all calendars are enabled, fetch and use all calendars
        if self.settings.get('enable_all_calendars'):
            self.log.info('All calendars enabled')
            for calendar in calendar_list['items']:
                calendar_id_list.append(calendar['id'])
        # go through list of enabled calendars
        else:
            self.log.info('Enabled calendars are {}'.format(self.enabled_calendars))
            for calendar in calendar_list['items']:
                if calendar['summary'] in self.enabled_calendars:
                    calendar_id_list.append(calendar['id'])
                    self.log.info('Added {} to calendar list'.format(calendar['summary']))

        # if no calendars enabled, default to primary
        if not calendar_id_list:
            self.log.info('No recognized calendars; focusing on primary')
            calendar_id_list.append('primary')

        event_items = []
        for calendar_id in calendar_id_list:
            event_list = self.service.events().list(calendarId=calendar_id,
                    timeMin=now_str, timeMax=day_end_str, singleEvents=True,
                    timeZone=self.timezone).execute()

            for event in event_list['items']:
                event_items.append(event)


        # sort event items by start date and time
        event_items.sort(key = lambda event: event['start']['dateTime'])

        return event_items 

    def speak_24h(self, event_list):

        for event in event_list:
            start_full = event['start'].get('dateTime')
            event_dict = {"event_summary": event['summary'],
                         "event_start_hr": start_full[11:13],
                         "event_start_min": start_full[14:16],
                         "meridian": ""}

            if event_dict.get('start_min')[0] == '0':
                if event_dict.get('start_min')[1] == '0':
                    self.speak_dialog('event.is.at.hundred', event_dict)
                else:
                    self.speak_dialog('event.is.at.oh', event_dict)
            else:
                self.speak_dialog('event.is.at', event_dict)

    def speak_12h(self, event_list):
        for event in event_list:
            start_full = event['start'].get('dateTime')
            event_dict = {"event_summary": event['summary'],
                         "event_start_hr": int(start_full[11:13]),
                         "event_start_min": int(start_full[14:16]),
                         "meridian": "a.m."}
                    
            # change to p.m. if the hour is large
            if event_dict.get('event_start_hr') >= 12:
                event_dict['event_start_hr'] -= 12
                event_dict['meridian'] = 'p.m.'

            # set '00' to '12'; note that above block sets
            # 12 p.m. to 00 p.m.
            if event_dict.get('event_start_hr') == 0:
                event_dict['event_start_hr'] = 12

            if event_dict.get('event_start_min') == 0:
                self.speak_dialog('event.is.at.oh.clock', event_dict)
            elif event_dict.get('event_start_min') < 10:
                self.speak_dialog('event.is.at.oh', event_dict)
            else:
                self.speak_dialog('event.is.at', event_dict)



def create_skill():
    return GoogleCalendar()


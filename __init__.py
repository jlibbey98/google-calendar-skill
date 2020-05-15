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
            for event in event_list:
                start_full = event['start'].get('dateTime',
                                    event['start'].get('date'))
                start_abbr = start_full[11:16]

                if start_abbr[3] == '0':
                    if start_abbr[4] == '0':
                        self.speak_dialog('event.is.at.hundred',
                                {"event_summary": event['summary'],
                                "event_time_start": start_abbr})
                    else:
                        self.speak_dialog('event.is.at.oh',
                                {"event_summary": event['summary'],
                                "event_time_start_h": start_abbr[0:2],
                                "event_time_start_m": start_abbr[4]})
                else:
                    self.speak_dialog('event.is.at', {"event_summary":
                            event['summary'], "event_time_start": start_abbr})
        else:
            self.speak_dialog('no.events.today')


    def update_credentials(self):
        """
        Acquires the credentials for the Google Calendar and uses them to
        build the service
        """
      
        credential_path = os.path.join(self.dep_dir, 'calendar_nd.json')

        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()

        http = credentials.authorize(httplib2.Http())

        self.service =  discovery.build('calendar', 'v3', http=http)


    def update_timezone(self):

        settings = self.service.settings().list().execute()

        for setting in settings['items']:
            if setting.get('id') == 'timezone':
                self.timezone = pytz.timezone(setting.get('value'))
                return

    def update_enabled_calendars(self):

        self.enabled_calendars = self.settings.get('enabled_calendar_list').split(',')
        

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
                    self.log.info('Added {} to calendar list'.format(calendar['id']))

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



def create_skill():
    return GoogleCalendar()


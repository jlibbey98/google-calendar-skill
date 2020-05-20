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

from mycroft import MycroftSkill
from mycroft import intent_handler
from adapt.intent import IntentBuilder

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

    @intent_handler(IntentBuilder('WhatIsToday')
                    .require('What')
                    .require('Scheduled')
                    .require('Today'))
    def handle_what_is_today(self, message):
        self.speak_dialog('let.me.check')

        # Fetch datetimes for today and convert them to strings
        now_dt = datetime.datetime.now(self.timezone)
        day_end_dt = now_dt.replace(hour=23, minute=59, second=59)

        now_str = now_dt.isoformat()
        day_end_str = day_end_dt.isoformat()
       
        # Fetch event list
        event_list = self.get_events(now_str, day_end_str)

        if event_list:
            self.speak_dialog('today.you.have')
            if self.settings.get('en_24h_clock'):
                self.speak_24h(event_list)
            else:
                self.speak_12h(event_list)                            
        else:
            self.speak_dialog('no.events.today')

    @intent_handler(IntentBuilder('WhatIsToday')
                    .require('What')
                    .require('Scheduled')
                    .require('Tomorrow'))
    def handle_what_is_today(self, message):
        self.speak_dialog('let.me.check')

        # Fetch datetimes for today and convert them to strings
        now_dt = datetime.datetime.now(self.timezone)

        tomorrow_start_dt = now_dt.replace(hour=0, minute=0, second=0)
        tomorrow_end_dt = now_dt.replace(hour=23, minute=59, second=59)

        tomorrow_start_dt = tomorrow_start_dt + datetime.timedelta(days=1)
        tomorrow_end_dt = tomorrow_end_dt + datetime.timedelta(days=1)

        tomorrow_start_str = tomorrow_start_dt.isoformat()
        tomorrow_end_str = tomorrow_end_dt.isoformat()
       
        # Fetch event list
        event_list = self.get_events(tomorrow_start_str, tomorrow_end_str)

        if event_list:
            self.speak_dialog('tomorrow.you.have')
            if self.settings.get('en_24h_clock'):
                self.speak_24h(event_list)
            else:
                self.speak_12h(event_list)                            
        else:
            self.speak_dialog('no.events.tomorrow')

    def update_credentials(self):
        """
        Initialization subroutine that acquires the credentials for the
        Google Calendar and uses them to build the service
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
        """
        Initialization subroutine that acquires and stores the timezone
        from the calendar's settings, which assumes that the desired
        time zone is the same as that of the calendar.
        """

        settings = self.service.settings().list().execute()

        # Iterates through the settings until it finds 'timezone'
        for setting in settings['items']:
            if setting.get('id') == 'timezone':
                self.timezone = pytz.timezone(setting.get('value'))
                return

    def update_enabled_calendars(self):
        """
        Initialization subroutine takes the list of calendars from the
        settings and uses the commas to parse into a list of strings
        that will match the calendar 'summary'
        """

        self.enabled_calendars = self.settings.get('enabled_calendar_list').split(', ')
        

    def get_events(self, start_time, end_time):
        """
        Accesses a list of today's events

        :param start_time: Beginning of time interval as a string
        :param end_time: End of time interval as a string
        :return: A list of event objects for today's events
        """

        # Fetch list of all calendars to compare with enabled calendars
        calendar_list = self.service.calendarList().list().execute()
        calendar_id_list = []

        # If all calendars are enabled, fetch and use all calendars
        if self.settings.get('enable_all_calendars'):
            self.log.info('All calendars enabled')
            for calendar in calendar_list['items']:
                calendar_id_list.append(calendar['id'])
        # Go through list of enabled calendars if there is no override
        else:
            self.log.info('Enabled calendars are {}'.format(self.enabled_calendars))
            for calendar in calendar_list.get('items'):
                if calendar.get('summary') in self.enabled_calendars:
                    calendar_id_list.append(calendar.get('id'))

        # If no calendars are enabled, default to primary
        if not calendar_id_list:
            calendar_id_list.append('primary')

        event_items = []

        # Fetch a list of events from each enabled calendar
        for calendar_id in calendar_id_list:
            event_list = self.service.events().list(calendarId=calendar_id,
                    timeMin=start_time, timeMax=end_time, singleEvents=True,
                    timeZone=self.timezone).execute()

            # Append events to a master list across all calendars
            for event in event_list['items']:
                event_items.append(event)


        # Sort event items by start date and time
        event_items.sort(key = lambda event: event['start']['dateTime'])

        return event_items 

    def speak_24h(self, event_list):
        """
        Subroutine to execute dialog for events with a 24-hour clock

        :param event_list: A list of event objects to be spoken by Mycroft
        """

        for event in event_list:
            # Extract the start time string
            start_full = event['start'].get('dateTime')

            # Use start time string and event 'summary' to create a
            # dictionary of arguments for the dialog
            event_dict = {"event_summary": event.get('summary'),
                         "event_start_hr": start_full[11:13],
                         "event_start_min": start_full[14:16],
                         "meridian": ""}

            # If the minute portion starts with zero, override Mycroft
            # to pronounce appropriate zeros
            if event_dict.get('start_min')[0] == '0':
                # If two zeros, pronounce 'hundred'
                if event_dict.get('start_min')[1] == '0':
                    self.speak_dialog('event.is.at.hundred', event_dict)
                # If only one zero, pronounce 'oh ___'
                else:
                    self.speak_dialog('event.is.at.oh', event_dict)
            # If no zeros, read numbers directly
            else:
                self.speak_dialog('event.is.at', event_dict)

    def speak_12h(self, event_list):
        """
        Subroutine to execute dialog for events with a 12-hour clock

        :param event_list: A list of event objects to be spoken by Mycroft
        """

        for event in event_list:
            # Extract the start time string
            start_full = event['start'].get('dateTime')

            # Use start time string and event 'summary' to create a
            # dictionary of arguments for the dialog
            event_dict = {"event_summary": event['summary'],
                         "event_start_hr": int(start_full[11:13]),
                         "event_start_min": int(start_full[14:16]),
                         "meridian": "a.m."}
                    
            # Change to p.m. if the hour is large and set hour
            # between 1 and 12
            if event_dict.get('event_start_hr') >= 12:
                event_dict['event_start_hr'] -= 12
                event_dict['meridian'] = 'p.m.'

            # Set '00' to '12'; note that above block sets 12 p.m.
            # to 00 p.m.
            if event_dict.get('event_start_hr') == 0:
                event_dict['event_start_hr'] = 12

            # Override Mycroft dialog with 'oh clock' if minute is zero
            if event_dict.get('event_start_min') == 0:
                self.speak_dialog('event.is.at.oh.clock', event_dict)
            # Override Mycroft dialog to say 'oh ___' if minute is single digit
            elif event_dict.get('event_start_min') < 10:
                self.speak_dialog('event.is.at.oh', event_dict)
            # Otherwise speak numbers normally
            else:
                self.speak_dialog('event.is.at', event_dict)



def create_skill():
    return GoogleCalendar()


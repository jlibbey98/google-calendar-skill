from mycroft import MycroftSkill, intent_file_handler


class GoogleCalendar(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('calendar.google.intent')
    def handle_calendar_google(self, message):
        self.speak_dialog('calendar.google')


def create_skill():
    return GoogleCalendar()


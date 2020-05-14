import datetime
import oauth2client

def get_events(service):
    """
    Retrieves a list of Google Calendar events for the day;
    input for 'service' is the credentials returned from
    get_credentials.py module. Returns a list of events
    """
    
    now_dt = datetime.datetime.utcnow()
    day_end_dt = now_dt.replace(hour=23, minute=59, second=59)

    now_str = now_dt.isoformat() + 'Z'
    day_end_str = day_end_dt.isoformat() + 'Z'

    event_list = service.events().list(calendarId='primary', timeMin=now_str,
                    timeMax=day_end_str, singleEvents=True, orderBy='startTime')
    events_result = event_list.execute()

    return events_result.get('items', [])

import datetime

from custom_tools.get_credentials import get_credentials
from custom_tools.get_events import get_events
from custom_tools.get_settings import get_settings

creds = get_credentials()

get_events(creds)
get_settings(creds)




import streamlit as st
import requests
import parameters as p
from bs4 import BeautifulSoup
import time
import json

##################################### Fetch general and service-specific parameters ################################

def error_handling_decorator(max_retries=3, sleep_interval=5, default_return=None):
    def decorator(base_func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries): 
                try:
                    result = base_func(*args, **kwargs)
                    return result
                except requests.exceptions.HTTPError as http_err:
                    if 400 <= http_err.response.status_code < 500:
                        print(f"Bad request. Check your parameters - No retry:{http_err}")
                        return default_return
                    print(f"server error ({http_err.response.status_code}) on attempt {attempt + 1}: {http_err}")
                    st.toast(f"Serverfehler ⚠️, wird erneut versucht {attempt + 1}/{max_retries}", icon="⏳")
                    time.sleep(sleep_interval)

                except requests.exceptions.RequestException as req_err:
                    print(f"Network error on attempt {attempt + 1}: {req_err}")
                    st.toast(f"Verbindungsfehler ⚠️, wird erneut versucht {attempt + 1}/{max_retries}", icon="⏳")
                    time.sleep(sleep_interval)

                except json.JSONDecodeError:
                    print(f"Data parsing error on attempt {attempt + 1}")
                    st.toast(f"ungeeignete Antwort vom Server ⚠️, wird erneut versucht {attempt + 1}/{max_retries}", icon="⏳")
                    time.sleep(sleep_interval)
                
                except Exception as e:
                    print(f"Unexpected error occurred: {e}")
                    return default_return
            print(f"{base_func.__name__}: All retries failed!")
            return default_return
        return wrapper
    return decorator

###############################################################################################################################

@error_handling_decorator(default_return={})
def get_office_params(headers=None):
    """Fetches the general settings for the website or the selected office"""

    url_settings = f"https://www.etermin.net/api/settingbs?t="

    settings_response = requests.get(url_settings, headers=headers, timeout=10)
    settings_response.raise_for_status()

    if not settings_response.json():
        print("No settings fetched!")
        return {}
    settings_json = settings_response.json()[0]  # because the server returns a json array with only one element
    settings_dict = {}

    settings_dict["language"] = settings_json.get("defaultlanguage", "de")
    settings_dict["appfuture"] = settings_json.get("appfuture", 0)
    settings_dict["appdeadline"] = settings_json.get("appdeadline", 0)
    settings_dict["appdeadlinewm"] = settings_json.get("appdeadlinewm", 0)
    settings_dict["msdcm"] = settings_json.get("msdcm", 0)
    settings_dict["caching"] = settings_json.get("caching", False)
    settings_dict["cluster"] = settings_json.get("cluster", False)
    settings_dict["limitappointments"] = settings_json.get("limitappointments", 0)
    settings_dict["limitappointmentstype"] = settings_json.get("limitappointmentstype", 0)
    settings_dict["onetimebooking"] = settings_json.get("onetimebooking", False)
    settings_dict["latf"] = settings_json.get("latf", 0)
    settings_dict["z"] = settings_json.get("z")
    settings_dict["agb"] = settings_json.get("agb", False)
    settings_dict["agblink"] = settings_json.get("agblink", "")
    settings_dict["dp"] = settings_json.get("dp", False)
    settings_dict["dplink"] = settings_json.get("dplink", False)
    settings_dict["nea"] = settings_json.get("nea", 0)
    settings_dict["enablefeedback"] = settings_json.get("enablefeedback", False)
    settings_dict["street"] = settings_json.get("street", "")
    settings_dict["zip"] = settings_json.get("zip", "")
    settings_dict["city"] = settings_json.get("city", "")
    settings_dict["timezone"] = settings_json.get("timezone", "")
    settings_dict["canceldeadline_settings"] = settings_json.get("canceldeadline")
    settings_dict['appointmentreminderhours'] = settings_json.get("appointmentreminderhours")
    settings_dict['appointmentreminderhours2'] = settings_json.get("appointmentreminderhours2")
    settings_dict['customerconfirm'] = settings_json.get("customerconfirm")
    settings_dict['customerconfirmtime'] = settings_json.get("customerconfirmtime")
    settings_dict['bl'] = settings_json.get("bl")
    settings_dict['storeip'] = settings_json.get("storeip")
    settings_dict['apw'] = settings_json.get('apw')
    settings_dict['showreminder'] = settings_json.get('showreminder')
    settings_dict['vfields'] = settings_json.get('vfields')
    settings_dict['vservices'] = settings_json.get('vservices')
    settings_dict['fillcalendarstrategy'] = settings_json.get('fillcalendarstrategy', 0)
    settings_dict['settings_showavcap'] = settings_json.get('showavcap')
    print("General settings fetched successfully")

    return settings_dict
        
        
    
@error_handling_decorator(default_return={})
def get_services(headers=None, office=""):
    """Retrieve the service-specific parameters"""

    settings = get_office_params(headers=headers)
    if not settings:
        print("Aborting get_services because get_office_params failed!")
        return {}
    service_params = p.construct_services_params(headers['webid'], settings=settings, hamborn=True if office == 'Ausländerbehörde Hamborn' else False)
    url_services = f"https://www.etermin.net/api/servicegroupservice"

    services_response = requests.get(url_services, headers=headers, params=service_params, timeout=10)
    services_response.raise_for_status()

    services_json = services_response.json()
    groups_dict = {}

    for item in services_json:
        raw_group_name = item.get('sg') or ""
        raw_service_name = item.get('s') or ""

        raw_service_annotation = item.get('sa') or ""
        service_id = item.get('sid') 
        duration = item.get('duration') if item.get("showduration") else 0
        capacity = item.get('nrappsel') or item.get('capacitynonsel') or 1
        captype = item.get('captype')
        enablecapacity = item.get('enablecapacity', False)
        canceldeadline = item.get('canceldeadline')
        rh = item.get('rh')
        rh2 = item.get('rh2')
        cc = item.get('cc')
        cct = item.get('cct')
        abb = item.get('abb')
        lb = item.get('lb')
        limitappointments = item.get('la') if lb == 1 else settings['limitappointments']
        limitappointmentstype = item.get('lat') if lb == 1 else settings['limitappointmentstype']
        limitservice = service_id if item.get('ls') == 1 else 0
        msdcm = settings['msdcm'] if item.get('msdcm') == -1 else item.get('msdcm')
        price = item.get('price')
        addapphours = item.get('addapphours')
        fcs = item.get('fcs')
        service_showavcap = item.get('showavcap')

        if not raw_service_name or not service_id:
            print(f"warning in get_services function: Skipping an entry due to missing data in {headers['webid']}")
            continue # some entries are just to diaplay the groups without containig services, so we dont want them

        group_name = BeautifulSoup(raw_group_name, "html.parser").get_text().strip()
        service_name = BeautifulSoup(raw_service_name, "html.parser").get_text().strip()

        if group_name not in groups_dict:
            groups_dict[group_name] = {}
        if service_name not in groups_dict[group_name]:
            groups_dict[group_name][service_name] = {}
        groups_dict[group_name][service_name].update({
            **settings,
            "serviceid": service_id,
            "servicetext": service_name,
            "serviceannotation": raw_service_annotation,
            "servicegroup": group_name,
            'raw_group_name': raw_group_name,
            "duration": duration,
            "capacity": capacity,
            'captype': captype,
            'enablecapacity': enablecapacity,
            'canceldeadline_service': canceldeadline,
            'rh': rh,
            'rh2': rh2,
            'cc': cc,
            'cct': cct,
            'abb': abb,
            'limitappointments': limitappointments,
            'limitappointmentstype': limitappointmentstype,
            'limitservice': limitservice,
            'msdcm': msdcm,
            'price': price,
            'addapphours': addapphours,
            'fcs': fcs,
            'service_showavcap': service_showavcap
        })
    return groups_dict

        
###############################################################################################################################

######################################################## Fetch form ###########################################################
@error_handling_decorator(default_return="")
def fetch_form_fields(headers=None, params=None):
    url = "https://www.etermin.net/api/field"

    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()

    print("Form fetched successfully")
    return response.text

###############################################################################################################################

################################################ request appointment ##########################################################
@error_handling_decorator(default_return={})
def fetch_date_or_time_slots(headers=None, params=None):
    """Retrieve the dates, in which there avilable appointments are. Or retrive the available appointments in a specific date
    depending on the parameters passed."""
    url = "https://www.etermin.net/api/timeslots"

    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    if not data:
        print("No available dates or time slots")
        return {}
    if "rangesearch" in params: # if range search activated, it scans a range of dates for appointments like from 01.06 to 01.07
        dates = {"dates": []} # I adjusted the dates variable to match the default return in the decorator. the older version was just dates = [], so I had two default returns in this function
        for date in data:
            dates["dates"].append(date["start"].split("T")[0]) #start:"2026-05-29T00:00:00" --> 2026-05-29
        return dates
    slots = {} # if range search is not activated, it retrieves the available appointments in a specific date
    for slot in data:
        id_and_timeslot = slot["idandtimeslot"].split("|") # example: idandtimeslot:"90709|2026-05-29 08:50|2026-05-29 09:00|Fahrzeugzulassung|0"
        start_time = id_and_timeslot[1] # --> 2026-05-29 08:50
        end_time = id_and_timeslot[2] # --> 2026-05-29 09:00
        dict_key = start_time.split(" ")[1] # I made the start time the dict key to access the time slot 2026-05-29 08:50 --> 08:50
        slots[dict_key] = {
            'start': start_time,
            'end': end_time,
            'calendarid': id_and_timeslot[0], # --> 90709
            'calendarname': id_and_timeslot[3], #--> Fahrzeugzulassung
            'hash': slot['hv'],
            'ecap': slot['ecap'],
            'capmax': slot['capmax']
        }
    return slots

        
###############################################################################################################################

#################################################### Telegram #################################################################
@error_handling_decorator(default_return="")
def check_telegram_verification(bot_token, user_uuid):
    """Check Telegram updates for the specific code.
    Returns the Chat ID if found, otherwise returns None.
    Expected Telegram data structure
{'ok': True,
 'result': [{
        'message': {
                    'chat': {
                            'first_name': 'John',
                            'id': 34534534,
                            'type': 'private',
                            'username': 'johndoe334'
                            },
                    'date': 1780626181,
                    'entities': [{
                            'length': 6,
                            'offset': 0,
                            'type': 'bot_command'
                                }],
                    'from': {
                            'first_name': 'John',
                            'id': 34534534,
                            'is_bot': False,
                            'language_code': 'en',
                            'username': 'johndoe334'
                            },
                    'message_id': 70,
                    'text': '/start secret_code_here'
                    },
        'update_id': 114913269
             }]
}
        """
    
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()
    result_list = data.get("result", [])
    if not result_list:
        return ""
    for item in result_list:
        message = item.get("message", {})
        text = message.get('text', "")
        if text == f"/start {user_uuid}": # /start is the command sent by the user followed by the secret code
            return message.get("chat", {}).get("id")
    return""
        
@error_handling_decorator()
def send_telegram_notification(token, chat_id, message):
    """ This function sends a notification to the user via Telegram when an appointment slot is found."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }

    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()

    st.toast("Benachrichtigung erfolgreich gesendet!")
    return
        
###############################################################################################################################

################################################ Booking request ##############################################################
@error_handling_decorator(default_return=False)
def limit_reached_request(headers=None, params=None):
    """send a request to the server before booking, checking if the user has multiple reservations in the system"""
    url = "https://www.etermin.net/limitreached"

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    print("limit reached request processed successfully")
    result = response.json()
    if result == 0:
        print(f"Limit check passed ({result}). Ready to book")
        return True
    else:
        print(f"Limit reached! ({result}). you cannot book more appointments")
        return False


@error_handling_decorator(default_return={})  
def book_appointment(webid="", encoded_body=None, content_length=0):
    url = "https://www.etermin.net/api/appointment"
    # special header, different from the header chached in the session, that is why I execute it here
    headers = p.construct_headers(webid, booking=True, length=content_length)

    response = requests.post(url, headers=headers, data=encoded_body)
    response.raise_for_status()
    print("congrats, appointment booked successfully, please confirm it from your email!")
    result = response.json()
    return result

###############################################################################################################################

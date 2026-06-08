import streamlit as st
import time
from datetime import datetime
import random
import re 
import os
import json
import urllib.parse
from bs4 import BeautifulSoup
from constants import CONFIG_FILE
import request_handler as rh
import parameters as p

############################################ Session State Intialization ######################################################

def initialize_session_state():
    """ initializes all required session state variables"""

    default_values = {
        "current_page": "home_page",
        "selection": {
            "selected_office": "--Bitte wählen--",
            "selected_group": "--Bitte wählen--",
            "selected_service": "--Bitte wählen--"
        },
        "price": None,
        "selected_method": "Reservieren",
        "bot_running": False,
        "found_dates": [],
        "found_slots": {},
        "state_date_key": {},
        "user_data": {},
        "is_user_data_valid": False,
        "chat_id": load_chat_id(),
        "desired_time": "08:00 - 10:00",
        "decision": "Nein",
        "flash_messages": {},
        "booking_progress": {},
        "book_data": {}
    }

    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value

###############################################################################################################################

#################################################### Check Next Request #######################################################

def should_wait_cooldown():
    """ This function checks if the bot should wait before making the next request
      to avoid hitting the server too frequently"""
    
    now = time.time()
    remaining = int(st.session_state.next_check_time - now)
    if remaining > 0 and not st.session_state.found_dates:
        st.caption(f"Bot läuft... Nächster Check in {remaining} Sekunden.")
        return True
    return False

def set_next_check_time(check_interval):
    """ This function sets the next check time with a random jitter to avoid hitting the server at exact intervals,
      which can help prevent being rate-limited or blocked."""
    
    jitter = random.randint(-10, 10)
    current_interval = max(10, check_interval + jitter)
    next_check =  time.time() + current_interval
    return next_check

###############################################################################################################################

#################################################### Form Utils ###############################################################

def form_parser(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    divs = soup.find_all("div")
    extracted_fields = []

    for div in divs:
        field_info = {}
        retrieved_tag = div.find(["input", "select", "textarea"])
        if not retrieved_tag:
            continue
        mandatory_label = div.find("span", class_="mandatory")
        mandatory_tag = retrieved_tag.get("data-required") in ["true", "True"]
        label_tag = div.find("label")
        if label_tag:
            label_text = label_tag.get_text().strip()
            label = label_text[:-1].strip() if label_text.endswith('*') else label_text
            field_info["for"] = label_tag.get("for", "")
        else:
            label = retrieved_tag.get("placeholder") or retrieved_tag.get("name")
            field_info["for"] = ""
        field_info["label"] = label
        field_info['mandatory'] = bool(mandatory_label or mandatory_tag)
        field_info["type"] = retrieved_tag.name
        regex = retrieved_tag.get("data-regex", "")
        for i in range(-1, -len(regex) -1, -1):
            if regex[i] == "$":
                if i != -1:
                    regex = regex[:i+1]
                break
        field_info["Regex"] = regex

        if retrieved_tag.name == "select":
            options = retrieved_tag.find_all("option")
            field_info["options"] = [opt.get('value') for opt in options]
        extracted_fields.append(field_info)

    #print(json.dumps(extracted_fields, indent=4, ensure_ascii=False))
    return extracted_fields

def validating_user_input(form_fields, user_data):
    """ This function validates the user input data."""
    
    validated_data = {}
    for index, (key, value) in enumerate(user_data.items()):
        if form_fields[index].get("Regex"):
            print(key)
            print(form_fields[index].get("Regex"))
            is_match = re.fullmatch(form_fields[index]["Regex"], value, re.IGNORECASE)
            validated_data[key] = True if is_match else False

    if not all(validated_data.values()):
        string = "\n- ".join([f"{key} ungültig" if not value else "" for key, value in validated_data.items()])
        st.error("Bitte prüfen Sie Ihre Eingaben\n"+ string)
        return False
    else:
        st.success("Daten erfolgreich gespeichert!")
        st.session_state.user_data.update(user_data)
        return True

###############################################################################################################################

######################################################## Telegram Utils #######################################################

def load_chat_id():
    """ Function to load the chat ID from a JSON file if it exists """
    if os.path.exists(CONFIG_FILE):
        if os.path.getsize(CONFIG_FILE) > 0:
            with open(CONFIG_FILE, "r") as file:
                data = json.load(file)
                return data.get("chat_id")
    return None

def save_chat_id(chat_id):
    """ Function to save the chat ID to a local JSON file """
    data = {"chat_id": chat_id}
    with open(CONFIG_FILE, "w") as file:
        json.dump(data, file)

###############################################################################################################################

############################################# Booking Request Helpers #########################################################  

def desired_time_request(desired_time, headers=None, settings=None):
    """Search for the desired appointment time entered by the user. If it fails to find one, it take the first available
    appointment, if the user wants to."""

    user_start, user_end = desired_time.split(" - ") # desired_time like 08:00 - 10:00
    user_start_obj = datetime.strptime(user_start, "%H:%M").time()
    user_end_obj = datetime.strptime(user_end, "%H:%M").time()
    first_available_time = None
    for date in st.session_state.found_dates:
        if not st.session_state.found_slots.get(date):
            time_slot_params = p.date_or_time_slot_params(target_date=date, settings=settings)
            slots = rh.fetch_date_or_time_slots(headers=headers, params=time_slot_params)
            st.session_state.found_slots[date] = slots
        for available_time, value in st.session_state.found_slots[date].items(): # mentioned above, the key is the start time
            if not first_available_time:
                first_available_time = value
            available_time_obj = datetime.strptime(available_time, "%H:%M").time()
            if user_start_obj <= available_time_obj <= user_end_obj:
                print("I have found your desired time")
                return value
    if st.session_state.random_time == "Ja":
        print("first available time:", first_available_time)
        return first_available_time
    else:
        print("No availble time slots found according to your desire")
        return {}

def create_bookerinfo(user_data, form_data, show_reminder=False):
    entries = ['Anrede', 'Vorname', 'Name', 'Strasse', 'PLZ', 'Ort', 'Telefon', 'E-Mail', 'Geburtsdatum', 'Notes']
    for index, (_, value) in enumerate(user_data.items()):
            german_variant = form_data[index]["label"]
            entry_string = f'{german_variant}\t{value}\r\n'

            if german_variant in entries:
                entries_index = entries.index(german_variant)
                entries[entries_index] = entry_string
    
    entries = [entry for entry in entries if "\t" in entry]

    bookerinfo = "".join(entries)
    bookerinfo += "\t\r\n"
    if show_reminder:
        bookerinfo += "Terminerinnerung\t12 Stunden vor Termin\r\n"
    return bookerinfo

def construct_encoded_body(body=None, is_second_request=False, addapphours=0):
    seperate_parts = []
    for key, value in body.items():
        if is_second_request and addapphours > 0 and key == 'checkexist':
            print('checkexist ignored!')
            continue
        elif key in ["start", "end", "tzaccount", 'servicescapacity']:
            seperate_parts.append(f"{key}={value}")
        
        else:
            seperate_parts.append(urllib.parse.urlencode({key: value}, quote_via=urllib.parse.quote, safe='()'))
    if is_second_request and addapphours > 0:
        seperate_parts.append(f'addapphours={addapphours}')
    encoded_body = "&".join(seperate_parts)
    print('encoded_body:\n' + encoded_body)
    body_bytes = encoded_body.encode('utf-8')
    content_length = len(body_bytes)
    print('content_length:' , content_length)
    return encoded_body, content_length



###############################################################################################################################

################################################## UI Helpers #################################################################
def set_flash_message(msg_id, msg_text):
    if not st.session_state.flash_messages.get(msg_id, None):
        st.session_state.flash_messages[msg_id] = {
            "message": msg_text,
            "message_time": time.time()
        }

def construct_appointment_details(appointment_data=None, user_data=None, 
                                setting=None, book_respose_data=None,
                                sel_office="", sel_group="", sel_service=""): 
    
    start_date_obj = datetime.strptime(appointment_data['start'], "%Y-%m-%d %H:%M") # example: 2026-06-03 08:00 
    end_date_obj = datetime.strptime(appointment_data['end'], "%Y-%m-%d %H:%M") # example: 2026-06-03 08:20 

    return {
        'Amt 🏫': sel_office,
        'Gruppe 📋': sel_group,
        'Service 🛠️': sel_service,
        'Datum 📅': start_date_obj.date(), # --> 2026-06-03
        'Terminbeginn ​🏃‍♂️': start_date_obj.time(), # --> 08:00
        'Terminende 💃🏼': end_date_obj.time(), # --> 08:20
        'Terminort 🏢': f"{setting['street']}, {setting['zip']} {setting['city']}", #the place where you must attend to the appointment
        'Buchungsreferenz 🔢': book_respose_data['AdditionalInformation'],
        'Name ​🪪': f"{user_data['Salutation']} {user_data['FirstName']} {user_data['LastName']}", # Herr John Doe
        'Adresse 🏡': f"{user_data['Street']}, {user_data['ZIP']} {user_data['City']}", # some street 45433, New York
        'Telefonnummer ☎️': user_data['Phone'],
        'Email 📧': user_data['Email']
    }

def style_annotation(html_snippet):
    unimportant_html = r'<b><u>Hier klicken</u> und damit die Dienstleistung auswählen, dann \\*"weiter zur Terminwahl\\*"\.*</b><br><br>'


    html_snippet = re.sub(unimportant_html, "", html_snippet, flags=re.IGNORECASE)
        
    refined_html = re.sub(r'href=["\']?([^ >"\']+)["\']?', r'href="\1"', html_snippet)
    styled_snippet = f"""
    <div style="
        background-color: #1c83ff1a; 
        color: #0054a3; 
        padding: 16px; 
        border-radius: 8px; 
        border: 1px solid #cce5ff;
        font-family: sans-serif;
        font-size: 16px;
        margin-bottom: 15px;
">
    {refined_html}
</div>
"""
    return styled_snippet


def should_disable_button(*conditions):
    return not all(conditions)

###############################################################################################################################
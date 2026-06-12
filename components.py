import streamlit as st
import datetime
import utils
from constants import MY_BOT_USERNAME, MY_BOT_TOKEN, OFFICE_COLLECTION
import parameters as p
from fragments import generic_flash_message
import request_handler as rh
import phonenumbers
import uuid

################################################# Home Page #############################################

def render_homepage():
    st.title("Terminjäger in Duisburg 📅", text_alignment="center")
    st.subheader("Ich helfe dir, einen Termin zu finden!", text_alignment="center")
    
def office_change_callback():
    st.session_state.selection["selected_office"] = st.session_state.ui_selected_office # I got problem with redendering the right value without using the key ui_selected_office/group .. etc
    st.session_state.selection["selected_group"] = "--Bitte wählen--"
    st.session_state.selection["selected_service"] = "--Bitte wählen--"
    st.session_state.bot_running = False
    st.session_state.user_data = {}

def group_change_callback():
    st.session_state.selection["selected_group"] = st.session_state.ui_selected_group
    st.session_state.selection["selected_service"] = "--Bitte wählen--"

def service_change_callback():
    st.session_state.selection["selected_service"] = st.session_state.ui_selected_service

def render_office():
    options = ["--Bitte wählen--", *OFFICE_COLLECTION.keys()]
    prev_selected_office = st.session_state.selection.get('selected_office', "--Bitte wählen--")
    current_index = options.index(prev_selected_office) if prev_selected_office else 0
    st.selectbox("Behörde auswählen", options=options,  
                        index=current_index, disabled=st.session_state.bot_running,
                        key='ui_selected_office', on_change=office_change_callback)

def render_groups_of_services(options=None):
    if options is not None:
        options = ["--Bitte wählen--", *options]
        prev_group = st.session_state.selection.get("selected_group", "--Bitte wählen--")
        current_index = options.index(prev_group) if prev_group in options else 0
        st.selectbox("Dienstleistungsgruppe auswählen", options=options, 
                    index=current_index, disabled=st.session_state.bot_running,
                    key='ui_selected_group', on_change=group_change_callback)
    else:
        print("rendering groups: expecting an array but None is passed!")

def render_services(options=None):
    if options is not None:
        options = ["--Bitte wählen--", *options] 
        prev_service = st.session_state.selection.get("selected_service", "--Bitte wählen--")
        current_index = options.index(prev_service) if prev_service in options else 0
        st.selectbox("Dienstleistung auswählen", options=options,
                            index=current_index, disabled=st.session_state.bot_running,
                            key='ui_selected_service', on_change=service_change_callback)
    else:
        print("rendering services: expecting an array but None is passed!")


def render_continue_button(is_continue_disabled):
    st.button("weiter", disabled=is_continue_disabled, use_container_width=True, 
              on_click= lambda: st.session_state.update({"current_page": "work_page"}))
#########################################################################################################

########################################### Bot Control Buttons #########################################
def start_bot_callback():
    st.session_state.bot_running = True

    # When the bot runs again we want to reset all the previous found data 
    st.session_state.found_dates = {}
    st.session_state.found_slots = {}
    st.session_state.booking_progress = {}
    st.session_state.state_date_key = {}
    st.session_state.book_data = {}

def stop_bot_callback():
    st.session_state.bot_running = False

    # this session is created on the fly when the bot is running
    if st.session_state.get("next_check_time"):
        del st.session_state.next_check_time 

def change_interval_callback():
    if st.session_state.get("bot_running", False):
        st.toast("Der Bot wird den neuen Intervalwert beim nächsten Check verwenden")

def render_bot_control(bot_disabled, container):
    with container:
        st.slider("Abfrageinterval (Sekunden):", 30, 300, 60, width=300,
            key="seconds_key", on_change=change_interval_callback)        
        st.button("🚀 Bot starten", disabled=bot_disabled or st.session_state.bot_running, on_click=start_bot_callback)
        st.button("🛑 Bot stoppen", disabled=not st.session_state.bot_running, on_click=stop_bot_callback)

#########################################################################################################

############################################# Bot Settings ##############################################
    
def telegram_activation_callback(cookie, user_uuid):
    if st.session_state.chat_id:
        msg_text = "Du bist bereits verizifiert. Du brauchst nicht mehr hier zu klicken"
        utils.set_flash_message(1, msg_text)
    else:
        chat_id = rh.check_telegram_verification(MY_BOT_TOKEN, user_uuid)
        if chat_id:
            encrypted_chat_id = utils.encrypt_chat_id(chat_id)
            utils.set_encrypted_chat_id_cookie(cookie, encrypted_chat_id)
            st.session_state.chat_id = chat_id
            msg_text = "Telegram-Verifizierung erfolgreich! Du erhältst eine Benachrichtigung, sobald ein Termin gefunden wird."
            utils.set_flash_message(2, msg_text)

        else:
            msg_text = "Telegram-Verifizierung fehlgeschlagen. Bitte stelle sicher, dass du den Bot gestartet hast und versuche es erneut."
            utils.set_flash_message(3, msg_text)

def method_change_callback():
    st.session_state.selected_method = st.session_state.ui_selected_method

def desired_time_change_callback():
    st.session_state.desired_time = st.session_state.ui_desired_time

def decision_change_callback():
    st.session_state.decision = st.session_state.ui_decision

def render_radio():  
    st.markdown("##### Bot-Einstellungen")
    options = ["Reservieren", "Telegram Benachrichtigung"]
    prev_selected_method = st.session_state.get("selected_method", "Reservieren")
    current_index = options.index(prev_selected_method) if prev_selected_method in options else 0
    st.radio("Möchtest du den Termin direkt reservieren oder per Benachrichtigung informiert werden?", 
            options=options, index=current_index, horizontal=True, disabled=st.session_state.bot_running,
            key='ui_selected_method', on_change=method_change_callback)
    st.divider()


def render_reservation_options():
    time_options = ["08:00 - 10:00", "10:00 - 12:00", "12:00 - 14:00", "14:00 - 16:00"]
    prev_desired_time = st.session_state.get("desired_time", "08:00 - 10:00")
    current_index = time_options.index(prev_desired_time) 
    st.radio("Wähle deine gewünschte Uhrzeit aus", options=time_options, index=current_index, key='ui_desired_time', on_change=desired_time_change_callback)

    decision_options = ["Ja", "Nein"]
    prev_decision = st.session_state.get("decision", "Nein")
    current_index = decision_options.index(prev_decision)
    st.radio("Ich versuche, den passenden Termin für Sie zu finden. Falls es keinen gibt, möchtest du" \
            "trotzdem irgendeinen verfügbaren Termin reservieren lassen?", options= decision_options, 
            key='ui_decision', on_change=decision_change_callback)

def render_telegram_options(cookie):
    if "user_uuid" not in st.session_state:
        st.session_state.user_uuid = str(uuid.uuid4())
    telegram_link = f"https://t.me/{MY_BOT_USERNAME}?start={st.session_state.user_uuid}"
    st.write("Um Benachrichtigungen zu erhalten, klicke bitte auf den folgenden Link und starte eine Unterhaltung mit dem Bot:", )
    st.link_button("Telegram Bot aktivieren", telegram_link, disabled=st.session_state.bot_running)
    st.caption("Nachdem du den Bot aktiviert hast, klicke auf die Schaltfläche unten, um die Verifizierung abzuschließen.")
    st.button("Ich habe den Bot aktiviert", disabled=st.session_state.bot_running, on_click=telegram_activation_callback, args=[cookie, st.session_state.user_uuid])

    generic_flash_message([msg_id for msg_id in st.session_state.flash_messages.keys()])
#########################################################################################################

################################################# Form ##################################################
    
def render_form(form_fields):
    user_data = {}
    st.markdown("##### Reservierungsdaten")
    
    with st.form("Gib deine Daten ein"):
        is_disabled = True if st.session_state.get('selected_method', 'Reservieren') == "Telegram Benachrichtigung" else False
        for field in form_fields:
            if field["type"] == "select":
                options = field["options"]
                prev_title = st.session_state.get("user_data", {}).get(field["label"], "bitte wählen")
                selected_value = st.selectbox(f'{field["label"]} {"*" if field["mandatory"] else ""}', options=options, 
                                              disabled=is_disabled or st.session_state.bot_running,
                                              index=(options.index(prev_title) if prev_title in options else 0))
                user_data[field["for"]] = selected_value

            if field["type"] == "input":
                if field['for'] == "Birthday":
                    value = st.session_state.get("user_data", {}).get(field["for"], None)
                    if value:
                        value = datetime.datetime.strptime(value, "%d.%m.%Y")
                    entered_value = st.date_input(f'{field["label"]} {"*" if field["mandatory"] else ""}',
                                                  min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today(), 
                                                  disabled=is_disabled or st.session_state.bot_running,
                                                  value=value)
                    if entered_value:
                        entered_value = entered_value.strftime("%d.%m.%Y")
                    user_data[field["for"]] = entered_value
                    continue

                entered_value = st.text_input(f'{field["label"]} {"*" if field["mandatory"] else ""}', 
                                                placeholder=field['label'],
                                                disabled=is_disabled or st.session_state.bot_running,
                                                value=st.session_state.get("user_data", {}).get(field["for"], ""))
                if entered_value and field["for"] == "Phone":
                    parsed_local_number = phonenumbers.parse(entered_value, "DE")
                    international_number = phonenumbers.format_number(parsed_local_number, phonenumbers.PhoneNumberFormat.E164)
                    entered_value = international_number

                user_data[field["for"]] = entered_value

            if field["type"] == "textarea":
                written_string = st.text_area(f'{field["label"]} {"*" if field["mandatory"] else ""}', disabled=is_disabled or st.session_state.bot_running,
                                              value=st.session_state.get("user_data", {}).get(field["for"], ""))
                user_data[field["for"]] = written_string

        submit_data = st.form_submit_button("Daten speichern", disabled=is_disabled or st.session_state.bot_running)
    return submit_data, user_data
            
#########################################################################################################

################################################# Status and Results ####################################

def fetch_slots_callback(state_key, date):
    current_state_key = st.session_state.state_date_key[state_key]
    for key in st.session_state.state_date_key:
        st.session_state.state_date_key[key] = False
    st.session_state.state_date_key[state_key] = not current_state_key

    if "found_slots" not in st.session_state:
        st.session_state.found_slots = {}
    if date not in st.session_state.found_slots:
        office = st.session_state.selection["selected_office"]
        group = st.session_state.selection["selected_group"]
        service = st.session_state.selection["selected_service"]
        settings = st.session_state[f"services_{office}"][group][service]
        headers = st.session_state[f"appointment_headers_{office}"]
        params = p.date_or_time_slot_params(target_date=date, settings=settings)
        st.session_state.found_slots[date] = rh.fetch_date_or_time_slots(headers=headers, params=params)

def render_status():
    if st.session_state.get("bot_running", False):
            st.info("Nach Termine im Hintergrund gesucht...")
            st.info(f"Überwachung für Dienst: {st.session_state.selection['selected_service']}"
                    +"\n\n" + f"in {st.session_state.selection['selected_office']}")
            
def render_results():
    if st.session_state.selected_method == 'Reservieren':
        if st.session_state.book_data:
            st.success("Whoooopa!! der Termin wurde erfolgreich gebucht. Es wurde dir eine Email geschickt. Bitte bestätige den Termin über den Link in deiner Email.")
            st.subheader("Termin Details")
            for key, value in st.session_state.book_data.items():
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.write(f"**{key}**")
                with col2:
                    st.write(f"{value}")
        if st.session_state.booking_progress:
            if st.session_state.booking_progress.get("server_response", False):
                st.error("Buchung fehlgeschlagen. Keine Bestätigung vom Server bekommen")

            if st.session_state.booking_progress.get("limit_reached", False):
                st.error("Termin gefunden, aber das Buchungslimit wurde erreicht. Versuche es bitte nochmal mit einem weiteren Termin!")

            if st.session_state.booking_progress.get("desired_time", False):
                st.info("Es gibt verfügbare Termine, die jedoch nicht deiner Wunschzeit entsprechen !!")
            st.button(" 🔄 erneut versuchen", on_click=start_bot_callback)


    if st.session_state.selected_method == 'Telegram Benachrichtigung':
        if st.session_state.found_dates.get("dates"):
            st.success("🎯 Löttchen Termine! 🕒")
            st.write("📅 **Verfügbare Termine für:**")
            cols = st.columns([1.5, 2.5])
            for key, value in st.session_state.selection.items():
                    if key == "selected_office":
                        with cols[0]:
                            st.write("**Amt 🏫**")
                        with cols[1]:
                            st.write(f"{value}")
                    elif key == "selected_group":
                        with cols[0]:
                            st.write("**Gruppe 📋**")
                        with cols[1]:
                            st.write(f"{value}")
                    else:
                        with cols[0]:
                            st.write("**Service 🛠️**")
                        with cols[1]:
                            st.write(f"{value}")
            if "state_date_key" not in st.session_state:
                st.session_state.state_date_key = {}
            cols = st.columns([1, 1, 1, 1])
            num_cols = len(cols)
            for index, date in enumerate(st.session_state.found_dates.get("dates", [])):
                state_key = f"expanded_{date}"
                if state_key not in st.session_state.state_date_key:
                    st.session_state.state_date_key[state_key] = False
                arrow_icon = "🔼" if st.session_state.state_date_key[state_key] else "🔽"
                col = cols[index % num_cols]
                with col:
                    st.button(f"{arrow_icon} {date} ✅", on_click=fetch_slots_callback, args=[state_key, date])
            st.divider()

def render_times():
    if st.session_state.selected_method == 'Telegram Benachrichtigung' and st.session_state.state_date_key:
        cols = st.columns([1, 1, 1, 1])
        num_cols = len(cols)
        
        date = [key for key, value in st.session_state.state_date_key.items() if value]
        if date:
            for index, (_, value) in enumerate(st.session_state.found_slots[date[0].split("_")[1]].items()):
                col = cols[index % num_cols]
                with col:
                    st.write(f"von {value['start'].split(' ')[1]} bis {value['end'].split(' ')[1]} ✅")
import streamlit as st
import extra_streamlit_components as stx
import components as comp
import request_handler as rh
import utils
import parameters as p
from fragments import check_appointments
from constants import OFFICE_COLLECTION

cookie = stx.CookieManager() 
st.set_page_config(page_title="Duisburg Termin Bot", page_icon="📅", layout="wide")

utils.initialize_session_state(cookie)

############################################### Home Page ############################################################
if st.session_state.current_page == "home_page":
    comp.render_homepage()
    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        st.markdown("##### Suchfilter")
        st.info("Bitte wähle das Amt, die Gruppe, in der sich der gewünschte Service befindet, und den Service, in dem du einen Termin buchen möchtest.") 
        comp.render_office()

        if st.session_state.selection.get("selected_office", "--Bitte wählen--") != "--Bitte wählen--":
            office = st.session_state.selection["selected_office"]
            webid = OFFICE_COLLECTION.get(office)[0]
            header_key = f"appointment_headers_{office}"
            services_key = f"services_{office}"
            if not st.session_state.get(header_key, {}): 
                # I am storing the header in the session to avoid creating it with every get request
                st.session_state[header_key] = p.construct_headers(webid)
                
            if not st.session_state.get(services_key, {}):
                # Cahing the settings parameters so we do not need to fetch it with every rerun
                with st.spinner("Lade verfügbare Dienstleistungen..."):
                    st.session_state[services_key] = rh.get_services(headers=st.session_state[header_key], office=office)
            groups_dict = st.session_state.get(services_key)
            if groups_dict:
                group_options = groups_dict.keys()
                comp.render_groups_of_services(options=group_options)

                if st.session_state.selection.get("selected_group", "--Bitte wählen--") != "--Bitte wählen--":
                    group = st.session_state.selection["selected_group"]
                    services_dict = groups_dict.get(group)
                    if services_dict:
                        service_options = services_dict.keys()
                        comp.render_services(options=service_options)
                        if st.session_state.selection.get("selected_service", "--Bitte wählen--") != "--Bitte wählen--":
                            service = st.session_state.selection["selected_service"]
                            st.session_state.price = st.session_state[services_key][st.session_state.selection["selected_group"]][service].get('price')
                        if st.session_state.selection.get("selected_service", "--Bitte wählen--") == "--Bitte wählen--":
                            st.info("Bitte wähle eine Dienstleistung aus, um fortzufahren.")
                else:
                    st.info("Bitte wähle eine Dienstleistungsgruppe aus, um fortzufahren.")
        else:
            st.info("Bitte wähle eine Behörde aus, um fortzufahren.")

        is_continue_disabled = utils.should_disable_button((st.session_state.selection["selected_office"] != '--Bitte wählen--'),
                                                            (st.session_state.selection["selected_group"] != '--Bitte wählen--'),
                                                            (st.session_state.selection["selected_service"] != '--Bitte wählen--'))
        comp.render_continue_button(is_continue_disabled)
        if st.session_state.selection.get("selected_service") != "--Bitte wählen--":
            annontation = st.session_state[services_key][st.session_state.selection["selected_group"]][st.session_state.selection["selected_service"]]['serviceannotation']
            if annontation:
                styled_annotation = utils.style_annotation(annontation)
                if styled_annotation:
                    st.markdown(styled_annotation, unsafe_allow_html=True)
                    
######################################################################################################################

######################################################### Work Page ##################################################

if st.session_state.current_page == "work_page":

######################################################### Bot control ################################################
    with st.container(border=True,horizontal=True, horizontal_alignment="distribute"):
        with st.container():
            st.button("⏪ zurück", on_click= lambda: st.session_state.update({"current_page": "home_page"}))
        bot_control_container = st.container(horizontal=True, horizontal_alignment="distribute")

######################################################################################################################
    col1, col2, col3 = st.columns([1, 1, 2], gap="medium") 

######################################################### Column 1 : Bot Settings ####################################
    
    with col1:
        comp.render_radio()
        if st.session_state.selected_method == 'Reservieren':
            if st.session_state.price is not None and st.session_state.price > 0:
                st.warning("Der ausgewählte Service ist kostenpflichtig, und muss online bezahlt werden. Reserviere bitte den Termin über die Website" \
                "oder wähle Telegram Benachrichtigung aus, um eine Nachricht über verfügbaren Termine zu bekommen!")
            comp.render_reservation_options()
            st.divider()
        if st.session_state.selected_method == "Telegram Benachrichtigung":
            comp.render_telegram_options(cookie)
            st.divider()

######################################################################################################################

######################################################### Column 2 : Form ############################################
   
    with col2:
        current = utils.get_current_settings()
        form_key = f"form_{current.office}"
        if form_key not in st.session_state:
            params = p.form_params(settings=current.settings)
            form_html = rh.fetch_form_fields(headers=current.headers, params=params)
            form_fields = utils.form_parser(form_html)
            st.session_state[form_key] = form_fields

        submit_data, user_data = comp.render_form(st.session_state[form_key])
        if submit_data:
            is_user_data_valid = utils.validating_user_input(st.session_state[form_key], user_data)
            st.session_state.is_user_data_valid = is_user_data_valid

    conditions = None
    if st.session_state.get('selected_method') == 'Reservieren':
        conditions = [st.session_state.is_user_data_valid, st.session_state.price is not None and st.session_state.price <= 0]
    elif st.session_state.get('selected_method') == 'Telegram Benachrichtigung':
        conditions = [bool(st.session_state.chat_id)]
    elif st.session_state.get('selected_method') == 'Verfügbare Termine angucken':
        conditions = [True]
    else:
        conditions = [False]
    is_start_button_disabled = utils.should_disable_button(*conditions)
    comp.render_bot_control(is_start_button_disabled, bot_control_container)

#####################################################################################################################

######################################################## Column 3 : Status & Results ################################
    with col3:
        st.header("Status & Ergebnisse", text_alignment="center")

        comp.render_status()
        check_appointments()
        comp.render_results()
        comp.render_times()
######################################################################################################################

        



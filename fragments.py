import streamlit as st
import time
import utils
from constants import OFFICE_COLLECTION, MY_BOT_TOKEN
import parameters as p
import request_handler as rh
import traceback



@st.fragment(run_every=1)
def generic_flash_message(msg_ids):
    """
    Generic function takes the message key which is usually saved in the session_state and checks if it should disapear
    """
    for msg_id in msg_ids:
        if msg_id in st.session_state.flash_messages:
            msg_data = st.session_state.flash_messages[msg_id]
            time_passed = time.time() - msg_data["message_time"]
            
            if time_passed >= 3:
                del st.session_state.flash_messages[msg_id]
            else:
                st.error(msg_data["message"]) if msg_id == 3 else st.info(msg_data["message"])


@st.fragment(run_every=1)
def check_appointments():
    """Check for available appointments periodically and handle notification or automatic booking"""
    # Guard clause to exit early if the bot is not running, 
    # we don't want to execute any of the logic below if the bot is not running.
    if not st.session_state.get("bot_running", False):
        if "next_check_time" in st.session_state:
            del st.session_state["next_check_time"]
        return  
    if "next_check_time" not in st.session_state:
        st.session_state.next_check_time = time.time()

    # Check if we should wait before the next check to avoid hitting the server too frequently.
    if utils.should_wait_cooldown():
        return

    # If cooldown is over and do the get request to check for appointments.
    current = utils.get_current_settings()
    webid = OFFICE_COLLECTION[current.office][0] #like "stadt_duisburg_zul"
    params = p.date_or_time_slot_params(settings=current.settings)
    data = rh.fetch_date_or_time_slots(headers=current.headers, params=params)

    # if dates that contain appointmets found, send notification or book a desired appointment.
    if data:
        st.balloons()
        time.sleep(2) # to display the balloons
        st.session_state.found_dates = data
        try:
            if st.session_state.selected_method == 'Telegram Benachrichtigung':
                rh.send_telegram_notification(MY_BOT_TOKEN, st.session_state.chat_id,
                                            f"🎯 Löttchen Termine für {current.service} gefunden! 🕒\n\n📅 Verfügbare Termine:\n"
                                            + "\n".join(st.session_state.found_dates["dates"]))
                
            elif st.session_state.selected_method == 'Reservieren':
                desired_time = st.session_state.desired_time
                found_time = utils.desired_time_request(desired_time, headers=current.headers, settings=current.settings)

                if found_time:
                    user_data = st.session_state.user_data
                    params = p.limit_reached_params(date=found_time['start'], settings=current.settings, user_data=user_data)
                    can_book = rh.limit_reached_request(headers=current.headers, params=params)

                    if can_book:
                        show_reminder = current.settings['showreminder']
                        booker_info = utils.create_bookerinfo(user_data, current.form_data, show_reminder=show_reminder)
                        body= p.construct_book_data(webid, settings=current.settings, user_data=user_data,
                                                    form_data=current.form_data, appointment_data=found_time, 
                                                    booker_info=booker_info)
                        encoded_body, body_lenght = utils.construct_encoded_body(body=body)

                        book_response_data = rh.book_appointment(webid=webid, encoded_body=encoded_body, 
                                                                content_length=body_lenght)
                        
                        addapphours = current.settings.get('addapphours', 0)
                        if addapphours > 0:
                            encoded_body, body_lenght = utils.construct_encoded_body(body=body, is_second_request=True, 
                                                                                     addapphours=addapphours)
                            rh.book_appointment(webid=webid, encoded_body=encoded_body, 
                                                                content_length=body_lenght)
                            
                        if book_response_data and "AdditionalInformation" in book_response_data: # I only want the book reference from the booking-request respone 
                            st.session_state.book_data = utils.construct_appointment_details(appointment_data=found_time, setting=current.settings, 
                                                                user_data=user_data, book_response_data=book_response_data, 
                                                                sel_office=current.office, sel_group=current.group, sel_service=current.service)
                        else:
                            st.session_state.booking_progress["server_response"] = True
                    else:
                        st.session_state.booking_progress["limit_reached"] = True
                else:
                    st.session_state.booking_progress["desired_time"] = True
                        
        except Exception as e:
            print(f"an error occured during booking: {e}") 
            traceback.print_exc()
        finally:

            st.session_state.bot_running = False
            del st.session_state.next_check_time
            st.rerun()

                         
    #if cooldown is over and no slots found, set the next check time after sending a request with fetch_appointments.
    st.session_state.next_check_time = utils.set_next_check_time(st.session_state.seconds_key)

 
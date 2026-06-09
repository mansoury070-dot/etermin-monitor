from datetime import date
import uuid

def construct_services_params(webid, settings=None, hamborn=False):
    return {
        'cache': 1,
        'w': webid,
        'v': settings['vservices'],
        'lang': settings['language'],
        **({'servicegroupid': 117957} if hamborn else {})
    }

def construct_headers(webid, booking=False, length=0):
    return { 
        'Accept': 'application/json, text/plain',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        **({'content-length': str(length)} if booking else {}),
        'content-type': 'application/json',
        **({'origin': 'https://www.etermin.net'} if booking else {}),
        'Pragma': 'no-cache',
        'priority': 'u=1, i',
        'Referer': f'https://www.etermin.net/{webid}',
        'Sec-Ch-Ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
        'webid': webid,
    }

def date_or_time_slot_params(target_date="", settings={}):
    showavcap = None
    if settings["service_showavcap"] == -1:
        showavcap = settings["settings_showavcap"]
    elif settings["service_showavcap"] == 0:
        showavcap = 'false'
    elif settings["service_showavcap"] == 1:
        showavcap = 'true'

    return {
        'date': (target_date if target_date else date.today().isoformat()),
        'serviceid': settings['serviceid'],
        'capacity': 1,
        **({'rangesearch': 1} if not target_date else {}),
        'caching': settings['caching'],
        'duration': 0 if settings['captype'] == -1 else settings['duration'],
        'cluster': settings['cluster'],
        'slottype': 0,
        'fillcalendarstrategy': settings['fillcalendarstrategy'] if settings['fcs'] in [-1, "-1", None, ""] else settings['fcs'], 
        'showavcap': showavcap,
        'appfuture': settings['appfuture'],
        'appdeadline': settings['appdeadline'],
        'appdeadlinewm': settings['appdeadlinewm'],
        'oneoff': 'null', 
        'msdcm': settings['msdcm'],
        **(
            {
                'tz': 'W. Europe Standard Time',
                'tzaccount': 'W. Europe Standard Time'
            } if target_date else {}),
        'calendarid': '' 
    }

def form_params(settings=None):
    return {
        'output': 'html',
        'serviceid': settings['serviceid'],
        'lang': settings['language'],
        'v': settings['vfields'],
        'requestaccess': False,
        'cache': 1,
    }


def limit_reached_params(date="", settings={}, user_data={}):
    return {
        'startdate': date,
        'limitappointments': settings['limitappointments'],
        'latf': settings['latf'],
        'limitappointmentstype': settings['limitappointmentstype'],
        'onetimebooking': settings['onetimebooking'],
        'z': settings['z'],
        'email': user_data['Email'],
        'phone': user_data['Phone'],
        'lastname': user_data['LastName'],
        'birthday': user_data.get('Birthday', 'undefined'),
        'limitservice': settings['limitservice'],
        'company': user_data.get('Company', 'undefined'),
        'additional1': user_data.get('additional1', 'undefined'),
        'firstname': user_data['FirstName'],
    }

def get_customer_confirm(service_cc, setting_cc):
    if service_cc == -1:
        return setting_cc # in the general setting "customerconfirm": True or False
    elif service_cc == 0:
        return False
    else:
        return True

def construct_book_data(webid, settings={}, user_data={}, form_data=[], appointment_data={}, booker_info=""):
    cap_suffix = " (1)" if settings['captype'] == 0 else ""
    service_text_dynamic = f"{settings['servicetext']}{cap_suffix}"
    
    
    location = f"{settings['street']}, {settings['zip']} {settings['city']}"
    return {
        'language': settings['language'],
        'bookingtype': 'Internet',
        'bookingurl': f'https://www.etermin.net/{webid}',
        'agbaccepted': str(settings['agb']).lower(),
        'dataprivacyaccepted': str(settings['dp']).lower(),
        **({'nea': 1} if settings['nea'] != 0 else {}),
        'feedbackpermissionaccepted': 0, # they will send you an email to ask you about how was you appointment give us a feedback, I do not think that public offices in Germany care about your feedback
        'newsletter': 'false',
        'senddoimsg': 1,
        'services': f"{settings['serviceid']}",
        'servicestext': service_text_dynamic,
        'servicesinclsgtext': f"{settings['raw_group_name']}<br>{service_text_dynamic}",
        'FirstName': user_data['FirstName'],
        'LastName': user_data['LastName'],
        'Email': user_data['Email'],
        **({'Birthday': user_data['Birthday']} if user_data.get('Birthday', None) else {}),
        'Street': user_data['Street'],
        'ZIP': user_data['ZIP'],
        'City': user_data['City'],
        'Phone': user_data['Phone'],
        'Salutation': user_data['Salutation'],
        **({'Notes': user_data['Notes']} if "Notes" in user_data else {}),
        'bookerinfo': booker_info,
        'calendarname': appointment_data['calendarname'],
        'start': appointment_data['start'],
        'end': appointment_data['end'],
        'calendarid': appointment_data['calendarid'],
        'calname': appointment_data['calendarname'],
        'hash': appointment_data['hash'],
        'location': location,
        'tzaccount': settings['timezone'],
        'checkexist': 1,
        'pricegross': 0,
        'appgroup': str(uuid.uuid4()),
        'capacity': 1, # we want to book an appointment just for one person
        'servicescapacity': f'{{"{settings["serviceid"]}":"1"}}' if settings['enablecapacity'] else "",
        'servicescapacitydetails': f'{settings["servicetext"]}\t{1 if settings["enablecapacity"] else ""}\r\n',
        'canceldeadline': settings['canceldeadline_settings'] if settings['canceldeadline_service'] == -1 else settings['canceldeadline_service'],
        'sync': 1,
        'sendemail': 1,
        'appointmentreminderhours': settings['rh'] if settings['rh'] != 1 else settings['appointmentreminderhours'],
        'appointmentreminderhours2': settings['rh2'] if settings['rh2'] != 1 else settings['appointmentreminderhours2'],
        **(
            {
                'confirmappointment': 1,
                'confirmtime': settings['customerconfirmtime'] if settings['cc'] == -1 else settings['cct']
            } if get_customer_confirm(settings['cc'], settings['customerconfirm']) else {}
            ),
        **({'servicesabb': settings['abb']} if settings['abb'] else {}),
        'sendinvoice': 1,
        'nrappbooked': 1,
        'capused': str(appointment_data["ecap"]).lower(),
        'capmaxused': appointment_data['capmax'],
        **({'blacklist': 1} if settings['bl'] else {}),
        'customerconfirm': str(get_customer_confirm(settings['cc'], settings['customerconfirm'])).lower(),
        'calselid': -1,
        'lnm': 1,
        'emailm': 1,
        'storeip': str(settings['storeip']).lower(),
        'apw': str(settings['apw']).lower(),
        **({'addapphours': settings['addapphours']} if settings['addapphours'] > 0 else {})
    }


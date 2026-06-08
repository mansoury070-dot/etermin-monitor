# etermin-monitor

A Python-based automation bot equipped with a simple web interface. It is designed specifically to help foreigners in Duisburg easily find and secure appointments at the Ausländerbehörde (Foreigners' Office).
Due to the high demand and limited availability of appointments, this bot continuously monitors the booking system to catch newly opened or canceled slots.

## Features

- **Graphical User Interface (GUI)** with Streamlit
  A simple and user-friendly interface to configure settings and choose your preferred mode of operation.

- **Telegram Notification Mode**
  - Sends real-time notifications to your Telegram when appointments become available.
  - Displays a list of available dates.
  - Clicking on a specific date reveals the exact available time slots for that day

- **Auto-Booking Mode**
  - Allows the user to select a preferred time range. The bot automatically books the first available appointment within the selected time range.
  - Offers a fallback option: if the desired time is not found, the bot can automatically book the very first available appointment it encounters.

  - **Privacy First**: All personal data required for this mode is processed strictly locally in memory during the active session and is completely wiped upon page refresh or a new start of the bot. No data is stored or logged.

## Under The Hood
  The booking website does not use direct links with visible parameters. Instead, the website's JavaScript code dynamically generates the required parameters when a user clicks on an available time.
  To automate this, I reverse-engineered the JavaScript code to understand exactly how and under what conditions these parameters are created. I then replicated this entire logic inside my Python code to successfully simulate the booking process.
  Please note that I intentionally skipped extracting the functions for online payments and modifying existing appointments, as the bot is only focused on quickly finding and booking new slots.
  
## Project Scope and Limitations

- **Primary Use Case:**
  Optimized for catching hard-to-get appointments that appear randomly due to cancellations or new openings.

- **Current Limitations:**
  The bot is currently not optimized for standard services like `BÜRGERSERVICE`. Since those services have wider availability throughout the week, the bot's current lack of advanced date filtering makes it less suitable for them.

## TODO / Upcoming Features

- [ ] **Advanced Date Filtering:**
      Implement customizable filters to allow users to specify preferred dates, times, or specific days of the week, ensuring the bot only targets relevant slots.
- [ ] **Direct Telegram Booking:**
      Enable a feature where users can click on an available time slot directly within the Telegram notification to automatically execute the booking process.
- [ ] **In-App (UI) Direct Booking:**
      Add functionality to the web interface allowing users to instantly secure an appointment by simply clicking on an available time slot displayed in the dashboard.
- [ ] **Email Notifications with Booking Links:**
      Introduce an email alert system that instantly sends a notification containing a link to the available appointment or the corresponding department, allowing for quick action.


## Installation and Setup

To set up and run this project locally, you need to install the required dependencies.
1. Clone this repository:
   ```bash git clone https://github.com/mansoury070-dot/etermin-monitor.git```
2. Navigate to the project folder:
   ```bash cd etermin-monitor```
3. Install the required libraries:
   ```bash pip install -r requirements.txt```
4. Start the application:
   ```bash streamlit run app.py```
   or if it did not work
   ```bash python -m streamlit run app.py```  

------------------------------------------------

## Disclaimer

This project, including the script and all associated source code, is developed and provided strictly for educational and informational purposes only.

By downloading, cloning, or using this repository, you agree to the following terms:

1. No Liability: The author of this script assumes no responsibility or liability for how this code is used. Any actions taken using this script are solely at your own risk.

2. Modifications: The default request interval is intentionally set to a reasonable time to prevent server overload and simulate normal human behavior. If you modify the source code to decrease the request interval or send aggressive automated requests, you are solely responsible for any consequences. This includes, but is not limited to, IP bans, legal actions, or damage to the target servers.

3. Terms of Service: It is your responsibility to ensure that your use of this script complies with the Terms of Service of the target website. The author does not encourage, condone, or endorse any activities that violate server policies, overload public systems, or disrupt public services.

Use this tool responsibly and ethically.
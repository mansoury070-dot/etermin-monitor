# etermin-monitor

A Python-based automation bot equipped with a simple web interface. It is designed specifically to help foreigners in Duisburg easily find and secure appointments at the Ausländerbehörde (Foreigners' Office).
Due to the high demand and limited availability of appointments, this bot continuously monitors the booking system to snipe newly opened or canceled slots.

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

## Under The Hood
  The booking website does not use direct links with visible parameters. Instead, the website's JavaScript code dynamically generates the required parameters when a user clicks on an available time.
  To automate this, I reverse-engineered the JavaScript code to understand exactly how and under what conditions these parameters are created. I then replicated this entire logic inside my Python code to successfully simulate the booking process.
  Please note that I intentionally skipped extracting the functions for online payments and modifying existing appointments, as the bot is only focused on quickly finding and booking new slots.
  
## Project Scope and Limitations

- **Primary Use Case:**
  Optimized for sniping hard-to-get appointments that appear randomly due to cancellations or new openings.

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

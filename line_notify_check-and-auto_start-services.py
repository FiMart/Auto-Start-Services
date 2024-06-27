import os
import time
import subprocess
from datetime import datetime
import urllib.parse
import urllib.request  # Using urllib for HTTP requests

# Specify the Line Notify access token
line_notify_token = 'hLqCt7fa2QrYZfltKV5fAqtuvCO5GznvltzLyRcIPJr'

# Specify the Line Notify API URL
line_notify_api = 'https://notify-api.line.me/api/notify'

# Specify the directory for logging notifications
log_directory = "D:\\Line Notify\\Code Python"

# Ensure the directory exists
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# File path for logging notifications
log_file_path = os.path.join(log_directory, "services_log.txt")

# Create log file if it doesn't exist
if not os.path.exists(log_file_path):
    with open(log_file_path, "w") as file:
        file.write(
            f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - Log file created.\n"
        )

# Function to check if a service is running
def service_running(service):
    result = subprocess.run(["sc", "query", service], capture_output=True, text=True)
    return "RUNNING" in result.stdout

# Function to manage services
def service_info(action, service, pause):
    try:
        running = service_running(service)
        if action == "stop":
            if not running:
                return 0
            subprocess.run(["sc", "stop", service], capture_output=True, text=True)
            time.sleep(pause)
            running = service_running(service)
            if running:
                return 1
            return 0

        elif action == "start":
            if running:
                return 1
            subprocess.run(["sc", "start", service], capture_output=True, text=True)
            time.sleep(pause)
            running = service_running(service)
            if not running:
                return 0
            # Log only to console, skip LINE Notify
            log_message(
                f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - Checking {service}...",
                skip_line_notify=True
            )
            return 1

        elif action == "restart":
            if not running:
                return 0
            subprocess.run(["sc", "stop", service], capture_output=True, text=True)
            time.sleep(pause)
            subprocess.run(["sc", "start", service], capture_output=True, text=True)
            time.sleep(pause)
            running = service_running(service)
            if not running:
                return 0
            # Log only to console, skip LINE Notify
            log_message(
                f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - Checking {service}... Started Successfully.",
                skip_line_notify=True
            )
            return 1

        elif action == "status":
            if running:
                return 1
            else:
                return 0
        else:
            return 2
    except Exception as e:
        log_message(f"Error performing {action} on {service}: {e}")
        return 2

# Function to log messages
def log_message(message, skip_line_notify=False):
    console_messages.append(message)
    print(message)
    with open(log_file_path, "a") as file:
        file.write(message + "\n")
    if not skip_line_notify:
        # Send message to Line Notify
        send_line_notify(message)

# Function to send message to Line Notify using urllib
def send_line_notify(message):
    headers = {
        'Authorization': f'Bearer {line_notify_token}'
    }
    data = urllib.parse.urlencode({'message': message}).encode()
    try:
        req = urllib.request.Request(line_notify_api, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            # Do nothing with response here to remove Line Notify response logging
            pass
    except urllib.error.URLError as e:
        print(f"Error sending Line Notify: {e}")

# Code to check Windows Service
try:
    console_messages = []

    # List of services to check and restart if needed
    services = [
        {"hostname": "DESKTOP-3DNU4E4", "name": "AsusAppService"},
        {"hostname": "DESKTOP-3DNU4E4", "name": "LightingService"},
        {"hostname": "DESKTOP-3DNU4E4", "name": "AsHidCtrlService"},
        {"hostname": "DESKTOP-3DNU4E4", "name": "AsusMultiAntennaSvc"},
    ]

    # Change the order of stopping services
    stop_order = ["AsusAppService", "AsHidCtrlService", "LightingService", "AsusMultiAntennaSvc"] # Stop Fixed Services

    # Check statuses of all services
    service_statuses = {
        service["name"]: service_info("status", service["name"], 5)
        for service in services
    }

    # Check if any service is not running
    if any(status == 0 for status in service_statuses.values()):
        not_running_services = [
            service for service, status in service_statuses.items() if status == 0
        ]
        message = (
            f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - Services not running: {', '.join(not_running_services)}"
        )
        log_message(message)

        # Stop services in the specified order and log each stop
        for service_name in stop_order:
            service = next((serv for serv in services if serv["name"] == service_name), None)
            if service:
                stop_result = service_info("stop", service["name"], 5)
                log_message(
                    f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - {'Stopped' if stop_result == 0 else 'Failed to stop'} {service['name']}.",
                    skip_line_notify=True  # Skip LINE Notify for stop messages
                )

        # Restart services in order
        previous_service_running = True
        for service in services:
            if previous_service_running:
                for attempt in range(3):  # Retry up to 3 times
                    if service_info("start", service["name"], 5) == 1:
                        message = f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - {service['name']} started successfully."
                        log_message(message)
                        break
                    else:
                        log_message(
                            f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - Failed to start {service['name']}, attempt {attempt + 1}/3."
                        )
                        time.sleep(5)
                else:
                    message = (
                        f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - {service['name']} failed to start after 3 attempts."
                    )
                    log_message(message)
                    previous_service_running = False
            else:
                message = (
                    f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - Failed to start {service['name']} because previous service was not running."
                )
                log_message(message)

    # Final check to ensure all services are running
    final_statuses = {
        service["name"]: service_info("status", service["name"], 5)
        for service in services
    }

    not_running_final_services = [
        service for service, status in final_statuses.items() if status == 0
    ]

    if not_running_final_services:
        message = (
            f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - Services still not running after restart attempts: {', '.join(not_running_final_services)}"
        )
        log_message(message)
    else:
        message = (
            f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - All services are running."
        )
        log_message(message)

except Exception as e:
    error_message = (
        f"{datetime.now().strftime('%d/%m/%y %H:%M:%S')} - An error occurred: {str(e)}"
    )
    print(error_message)
    with open(log_file_path, "a") as file:
        file.write(error_message + "\n")
    # Send error message to Line Notify
    send_line_notify(error_message)

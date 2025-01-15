import subprocess
import time
import socket
from datetime import datetime

# ANSI escape codes for colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_welcome_message():
    hostname = socket.gethostname()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"""
{GREEN}====================================
    System Monitor Dashboard
===================================={RESET}
Server: {hostname}
Date: {current_time}

System status checks in progress...
""")

def check_service_status_with_uptime(services):
    results = []
    for service in services:
        try:
            # Check if the service is active
            output = subprocess.check_output(f"sudo systemctl is-active {service}", shell=True, universal_newlines=True).strip()
            if output == 'active':
                # Check the service uptime using 'systemctl show'
                uptime_output = subprocess.check_output(f"sudo systemctl show {service} --property=ActiveEnterTimestamp", shell=True, universal_newlines=True).strip()
                uptime = uptime_output.split("=", 1)[1] if "=" in uptime_output else "Unknown"
                results.append(f"{service:<20}: {GREEN}active (Uptime: {uptime}){RESET}")
            else:
                results.append(f"{service:<20}: {RED}not running{RESET}")
        except subprocess.CalledProcessError:
            results.append(f"{service:<20}: {RED}not found or not running{RESET}")
    return results

# Other system checks
def check_nginx_process():
    try:
        output = subprocess.check_output("ps -ef | grep '[n]ginx'", shell=True, universal_newlines=True).strip()
        if output:
            return f"nginx: {GREEN}running{RESET}"
        else:
            return f"nginx: {RED}not running{RESET}"
    except subprocess.CalledProcessError as e:
        return f"Error checking nginx process: {e}"

def check_zombie_processes():
    try:
        output = subprocess.check_output("ps aux | awk '{ if ($8 == \"Z\") print $0 }'", shell=True, universal_newlines=True)
        if output:
            return ["Zombie processes detected:", output]
        else:
            return ["No zombie processes found."]
    except subprocess.CalledProcessError as e:
        return [f"Error checking zombie processes: {e}"]

def check_disk_usage():
    try:
        output = subprocess.check_output("df -h", shell=True, universal_newlines=True)
        return [output]
    except subprocess.CalledProcessError as e:
        return [f"Error checking disk usage: {e}"]

def check_disk_usage_threshold(threshold=90):
    results = []
    try:
        output = subprocess.check_output("df -h --output=pcent,target", shell=True, universal_newlines=True).strip().splitlines()
        for line in output[1:]:  # Skip the header line
            usage, mount_point = line.strip().split()
            usage_percent = int(usage.strip('%'))
            if usage_percent >= threshold:
                results.append(f"{RED}ALERT: {mount_point:<30} is at {usage_percent}% usage!{RESET}")
        if not results:
            results.append(f"All disks are below the {threshold}% usage threshold.")
    except subprocess.CalledProcessError as e:
        results.append(f"Error checking disk usage threshold: {e}")
    return results

# Other system and custom service checks
def main():
    print_welcome_message()

    services_to_check = ['sshd', 'httpd', 'mysql']  # Removed 'nginx' from here
    results = []

    # Service Status with Uptime
    results.append(f"{BLUE}=== Service Status with Uptime ==={RESET}")
    results.extend(check_service_status_with_uptime(services_to_check))

    # Check Nginx using ps -ef | grep nginx
    results.append(f"\n{BLUE}=== Nginx Process Status ==={RESET}")
    results.append(check_nginx_process())

    # Zombie Processes
    results.append(f"\n{BLUE}=== Zombie Processes ==={RESET}")
    results.extend(check_zombie_processes())

    # Disk Usage
    results.append(f"\n{BLUE}=== Disk Usage ==={RESET}")
    results.extend(check_disk_usage())

    # Disk Usage Threshold
    results.append(f"\n{BLUE}=== Disk Usage Threshold ==={RESET}")
    results.extend(check_disk_usage_threshold(90))

    # Print the comprehensive report
    print("\n".join(results))

if __name__ == "__main__":
    main()

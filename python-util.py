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

def check_service_status(services):
    results = []
    for service in services:
        try:
            output = subprocess.check_output("sudo systemctl is-active {}".format(service), shell=True, universal_newlines=True).strip()
            if output == 'active':
                results.append("{:<20}: {}{}".format(service, GREEN, output + RESET))
            else:
                results.append("{:<20}: {}not running{}".format(service, RED, RESET))
        except subprocess.CalledProcessError:
            results.append("{:<20}: {}not found or not running{}".format(service, RED, RESET))
    return results

def check_nginx_process():
    try:
        output = subprocess.check_output("ps -ef | grep '[n]ginx'", shell=True, universal_newlines=True).strip()
        if output:
            return "nginx: {}running{}".format(GREEN, RESET)
        else:
            return "nginx: {}not running{}".format(RED, RESET)
    except subprocess.CalledProcessError as e:
        return "Error checking nginx process: {}".format(e)

def check_zombie_processes():
    try:
        output = subprocess.check_output("ps aux | awk '{{ if ($8 == \"Z\") print $0 }}'", shell=True, universal_newlines=True)
        if output:
            return ["Zombie processes detected:", output]
        else:
            return ["No zombie processes found."]
    except subprocess.CalledProcessError as e:
        return ["Error checking zombie processes: {}".format(e)]

def check_disk_usage():
    try:
        output = subprocess.check_output("df -h", shell=True, universal_newlines=True)
        return [output]
    except subprocess.CalledProcessError as e:
        return ["Error checking disk usage: {}".format(e)]

def check_disk_usage_threshold(threshold=90):
    results = []
    try:
        output = subprocess.check_output("df -h --output=pcent,target", shell=True, universal_newlines=True).strip().splitlines()
        for line in output[1:]:  # Skip the header line
            usage, mount_point = line.strip().split()
            usage_percent = int(usage.strip('%'))
            if usage_percent >= threshold:
                results.append("{}ALERT: {:<30} is at {}% usage!{}".format(RED, mount_point, usage_percent, RESET))
        if not results:
            results.append("All disks are below the {}% usage threshold.".format(threshold))
    except subprocess.CalledProcessError as e:
        results.append("Error checking disk usage threshold: {}".format(e))
    return results

def check_mounted_drive(drive_path):
    try:
        output = subprocess.check_output("df -h {}".format(drive_path), shell=True, universal_newlines=True).strip()
        if output:
            return [output + GREEN + " (Mounted)" + RESET]
        else:
            return ["{} not mounted or does not exist.".format(drive_path) + RED]
    except subprocess.CalledProcessError as e:
        return ["Error checking mounted drive: {}".format(e)]

def check_network_drive(network_drive):
    try:
        output = subprocess.check_output("df -h | grep {}".format(network_drive), shell=True, universal_newlines=True).strip()
        if output:
            return [network_drive + GREEN + " is mounted." + RESET]
        else:
            return ["ALERT: {} is not mounted or gone.".format(network_drive) + RED]
    except subprocess.CalledProcessError:
        return ["ALERT: {} is not mounted or gone.".format(network_drive) + RED]


def check_custom_services(custom_services):
    results = []
    for service in custom_services:
        try:
            output = subprocess.check_output("pgrep -fl {}".format(service), shell=True, universal_newlines=True).strip()
            if output:
                results.append("{:<20}: {}running{}".format(service, GREEN, RESET))
            else:
                results.append("{:<20}: {}not running{}".format(service, RED, RESET))
        except subprocess.CalledProcessError:
            results.append("{:<20}: {}not running{}".format(service, RED, RESET))
    return results

def check_firewalld():
    results = []
    try:
        status = subprocess.check_output("sudo systemctl is-active firewalld", shell=True, universal_newlines=True).strip()
        if status == 'active':
            results.append("firewalld: {}active{}".format(GREEN, RESET))
            rules = subprocess.check_output("firewall-cmd --list-all", shell=True, universal_newlines=True)
            results.append("firewalld rules:\n{}".format(rules))
        else:
            results.append("firewalld: {}inactive{}".format(RED, RESET))
    except subprocess.CalledProcessError:
        results.append("firewalld: {}not found or error checking{}".format(RED, RESET))
    return results

def check_ufw():
    results = []
    try:
        status = subprocess.check_output("sudo ufw status", shell=True, universal_newlines=True).strip()
        if "Status: active" in status:
            results.append("ufw: {}active{}".format(GREEN, RESET))
            rules = subprocess.check_output("ufw status verbose", shell=True, universal_newlines=True)
            results.append("ufw rules:\n{}".format(rules))
        else:
            results.append("ufw: {}inactive{}".format(RED, RESET))
    except subprocess.CalledProcessError:
        results.append("ufw: {}not found or error checking{}".format(RED, RESET))
    return results

def check_cpu_utilization():
    try:
        output = subprocess.check_output("top -bn1 | grep 'Cpu(s)'", shell=True, universal_newlines=True).strip()
        return ["CPU Utilization:\n{}".format(output)]
    except subprocess.CalledProcessError as e:
        return ["Error checking CPU utilization: {}".format(e)]

def check_memory_utilization():
    try:
        output = subprocess.check_output("free -h", shell=True, universal_newlines=True).strip()
        return ["Memory Utilization:\n{}".format(output)]
    except subprocess.CalledProcessError as e:
        return ["Error checking memory utilization: {}".format(e)]

def main():
    print_welcome_message()

    services_to_check = ['sshd', 'httpd', 'mysql']  # Removed 'nginx' from here
    custom_services_to_check = ['mwallet', 'integration', 'notification']
    drive_path = '/mnt/dosh-share-drive'
    network_drive = '//doshshareddrive.file.core.windows.net/dosh-share-drive'
    network_host = 'doshshareddrive.file.core.windows.net'  # The host to check connectivity

    results = []

    # Service Status
    results.append(f"{BLUE}=== Service Status ==={RESET}")
    results.extend(check_service_status(services_to_check))

    # SG Services
    results.append(f"\n{BLUE}=== SG Services Status ==={RESET}")
    results.extend(check_custom_services(custom_services_to_check))

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

    # Firewall Status
    results.append(f"\n{BLUE}=== Firewall Status ==={RESET}")
    results.extend(check_firewalld())
    results.extend(check_ufw())

    # CPU Utilization
    results.append(f"\n{BLUE}=== CPU Utilization ==={RESET}")
    results.extend(check_cpu_utilization())

    # Memory Utilization
    results.append(f"\n{BLUE}=== Memory Utilization ==={RESET}")
    results.extend(check_memory_utilization())

    # Print the comprehensive report
    print("\n".join(results))

if __name__ == "__main__":
    main()

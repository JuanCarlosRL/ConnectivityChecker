import csv
import os
import paramiko
import platform
import argparse

def ping(ip):
    param = "-c 1" if platform.system().lower() != "windows" else "-n 1"
    response = os.system(f"ping {param} {ip}")
    return response == 0

def ssh_connect(ip, port, username, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Attempting to connect to {ip}:{port} with username {username}")
        client.connect(ip, port=port, username=username, password=password, timeout=10)
        client.close()
        print(f"Access granted for {ip}")
        return "Access Granted"
    except paramiko.AuthenticationException:
        print(f"Access denied for {ip}: invalid credentials")
        return "Access Denied"
    except Exception as e:
        print(f"Connection failed for {ip}: {e}")
        return "Connection Failed"

def test_devices(file_path, test_type, selected_devices):
    print(f"Running test_devices with file_path: {file_path}, test_type: {test_type}, selected_devices: {selected_devices}")
    results = []
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            print(f"Processing row: {row}")
            if selected_devices and row["Name"] not in selected_devices:
                results.append(row)
                continue
            print("Running tests for device:", row["Name"])
            ip = row["IP"]
            port = int(row["Port"]) if row["Port"] else 22  # Use default port 22 if not specified
            username = row["Username"]
            password = row["Password"]
            result = {"Name": row["Name"], "IP": ip, "Ping": False, "Port": port, "SSH": False, "Username": username, "Password": password, "Access": False}

            if test_type in ["ping", "all"] and ping(ip):
                result["Ping"] = True
                if test_type == "ping":
                    result["SSH"] = row["SSH"]
                    result["Access"] = row["Access"]
            
            if (test_type == "ssh" and row["Ping"]) or (test_type == "all" and result["Ping"]):
                ssh_result = ssh_connect(ip, port, username, password)
                if ssh_result == "Access Granted":
                    result["SSH"] = True
                    result["Access"] = True
                elif ssh_result == "Access Denied":
                    result["SSH"] = True
                    result["Access"] = False
                else:
                    result["Access"] = False
                
                result["Ping"] = row["Ping"] if test_type == "ssh" else result["Ping"]
            
            results.append(result)
    
    print(f"Writing results to {file_path}")
    with open(file_path, mode='w', newline='') as file:
        fieldnames = ["Name", "IP", "Ping", "Port", "SSH", "Username", "Password", "Access"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(results)
    print("Finished writing results")

if __name__ == "__main__":
    print("Starting run_tests.py")
    parser = argparse.ArgumentParser(description="Test devices connectivity")
    parser.add_argument("file_path", type=str, help="Path to the CSV file")
    parser.add_argument("--test_type", type=str, choices=["all", "ping", "ssh"], default="all", help="Type of test to perform")
    parser.add_argument("--devices", type=str, nargs="*", help="List of devices to test")
    args = parser.parse_args()
    print(f"Arguments received: file_path={args.file_path}, test_type={args.test_type}, devices={args.devices}")
    test_devices(args.file_path, args.test_type, args.devices)

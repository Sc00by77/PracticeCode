"""
Network Device Discovery Tool
------------------------------
Broadcasts a discovery request and collects responses from network devices.

Real-world use: Similar to network scanners and device discovery tools
"""

import socket
import time

BROADCAST_IP = "255.255.255.255"
DISCOVERY_PORT = 5001
LISTEN_TIMEOUT = 3

print(" Device scanner tool")

discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

discovery_socket.settimeout(LISTEN_TIMEOUT)

discovery_message = "DISCOVER_DEVICE"

print(f" Broadcasting discovery request to {BROADCAST_IP}:{DISCOVERY_PORT}")
print(f" Message: {discovery_message}")
print(f" Listening for {LISTEN_TIMEOUT} seconds...\n")

discovery_socket.sendto(discovery_message.encode('utf-8'), (BROADCAST_IP, DISCOVERY_PORT))

discovered_devices = []
start_time = time.time()

while True:
  try:
    response_data, device_address = discovery_socket.recvfrom(1024)
    response = response_data.decode('utf-8')

    if response.startswith("DEVICE:"):
      device_data = response[7:].split('|')

      if len(device_data) == 4:
        device = {
          "ip_address": device_address[0],
          "hostname": device_data[0],
          "type": device_data[1],
          "model": device_data[2],
          "reported_ip": device_data[3]
        }

        discovered_devices.append(device)

        print(f" Device #{len(discovered_devices)}")
        print(f" IP Address #{(device['ip_address'])}")
        print(f" Hostname #{(device['hostname'])}")
        print(f" Type #{(device['type'])}")
        print(f" Model #{(device['model'])}")

  except socket.timeout:
    break

  except Exception as e:
    print(f" Error receiving response: {e}")
    break

elapsed_time = time.time() - start_time

print(f"Discovery complete!")
print(f"Found {len(discovered_devices)} device(s) in {elapsed_time:.2f} seconds")

discovery_socket.close()
print("\n Scanner tool closed!")
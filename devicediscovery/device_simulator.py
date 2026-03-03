"""
Network Device Simulator
------------------------
Simulates a network device (router/switch) that responds to discovery requests.
Run multiple instances to simulate multiple devices.

Real-world use: Similar to how Cisco Discovery Protocol (CDP) works
"""

import socket
import sys

LISTEN_IP = ""
DISCOVERY_PORT = 5001
DEVICE_TIMEOUT = 60

DEVICE_INFO = {
  "hostname": "Router-Office-1",
  "type": "Cisco Router",
  "model": "ISR-4331",
  "ip": "192.168.1.1"
}

if len(sys.argv) > 1:
  DEVICE_INFO["hostname"] = sys.argv[1]

device_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

device_socket.bind((LISTEN_IP, DISCOVERY_PORT))

device_socket.settimeout(DEVICE_TIMEOUT)

print(f"\n Network Device Simulator: {DEVICE_INFO['hostname']}")
print(f"Listening for discovery requests on port {DISCOVERY_PORT}")
print(f" Will respond for {DEVICE_TIMEOUT} seconds\n")

try:
  while True:
    data, sender_address = device_socket.recvfrom(1024)
    message = data.decode('utf-8')

    if message == "DISCOVER_DEVICE":
      print(f" Discovery request form {sender_address[0]}:{sender_address[1]}")

      response = f"DEVICE: {DEVICE_INFO['hostname']} | {DEVICE_INFO['type']} | {DEVICE_INFO['model']} | {DEVICE_INFO['ip']}"

      device_socket.sendto(response.encode('utf-8'), sender_address)
      print(f"\n Device information sent")

except socket.timeout:
  print(f"\n Error: No response with {DEVICE_TIMEOUT} seconds")

except KeyboardInterrupt:
  print("\n Stopped by user")

finally:
  device_socket.close()
  print(" Device simulatoe stopped")

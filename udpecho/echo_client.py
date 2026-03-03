"""
Simple UDP Echo Client
----------------------
This represents a monitoring tool or management application
that sends queries to network devices.

Real-world use: Similar to network monitoring tools that poll devices
"""

import socket

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000
CLIENT_TIMEOUT = 5

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

client_socket.settimeout(CLIENT_TIMEOUT)

print("UDP Echo Client")

message = "Hello from network monitoring too!"

print(f" Sending to {SERVER_IP}:{SERVER_PORT}")
print(f" Message: '{message}'")

client_socket.sendto(message.encode('utf-8'), (SERVER_IP, SERVER_PORT))

try:
  response_data, server_address = client_socket.recvfrom(1024)

  response = response_data.decode('utf-8')

  print(f"\n Recived message from {server_address[0]}:{server_address[1]}")
  print(f" Message: {message}")
  print("\n Communication successful!\n")

except socket.timeout:
  print(f"\n Error: No response with {CLIENT_TIMEOUT} seconds")
  print(f" There server might be down or unreachable\n")

except Exception as e:
  print(f"\n ERROR: {e}")

finally:
  client_socket.close()
  print("Socket closed\n")
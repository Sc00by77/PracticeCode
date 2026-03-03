"""
Simple UDP Echo Server
----------------------
This represents a network device (like a router or switch) 
that listens for queries and responds back.

Real-world use: Similar to how SNMP (Simple Network Management Protocol) agents work on network devices
"""

import socket

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000


server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_socket.bind((SERVER_IP, SERVER_PORT))

print(f" UDP Echo Server started")
print(f" Listening on {SERVER_IP}:{SERVER_PORT}")

try:
  while True:
    data, client_address = server_socket.recvfrom(1024)

    message = data.decode('utf-8')

    print(f"\n Received from {client_address[0]}:{client_address[1]}")
    print(f" Message: {message}")


    response = f"ECHO: {message}"

    server_socket.sendto(response.encode('utf-8'), client_address) 

    print(f" Sent response: '{response}'\n")
except KeyboardInterrupt:
  print("\n\n Server stpped by user")

finally:
  server_socket.close()
  print(" Socket closed\n")
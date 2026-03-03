"""
Simple TCP Chat Client
----------------------
Connects to the chat server and allows sending/receiving messages.

Real-world use: Similar to messaging app clients
"""

import socket
import threading
import sys

# Configuration
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5500

def receive_messages(client_socket):
    """
    Continuously receive and display messages from server.
    Runs in a separate thread so we can send and receive simultaneously.
    """
    while True:
        try:
            # Receive message from server
            message = client_socket.recv(1024).decode('utf-8')
            
            if not message:
                # Server closed connection
                print("\n Disconnected from server")
                break
            
            # Display the message
            print(message, end='')
            
        except:
            # Connection error
            print("\n Connection lost")
            break

def start_client():
    """
    Connect to chat server and start chatting.
    """
    # Step 1: Create TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    print("=" * 60)
    print("💬 TCP Chat Client")
    print("=" * 60)
    
    try:
        # Step 2: Connect to server
        print(f" Connecting to {SERVER_IP}:{SERVER_PORT}...")
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print("✓ Connected to server!\n")
        
        # Step 3: Start thread to receive messages
        receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
        receive_thread.daemon = True
        receive_thread.start()
        
        # Step 4: Main loop - send messages
        while True:
            # Get user input
            message = input()
            
            if message.strip().lower() == 'quit':
                print(" Goodbye!")
                break
            
            if message.strip():  # Only send non-empty messages
                # Send message to server
                client_socket.send(message.encode('utf-8'))
    
    except ConnectionRefusedError:
        print(f" Could not connect to server at {SERVER_IP}:{SERVER_PORT}")
        print("   Make sure the server is running!")
    
    except Exception as e:
        print(f" Error: {e}")
    
    finally:
        # Close connection
        client_socket.close()
        print("✓ Disconnected\n")

# Run the client
if __name__ == "__main__":
    start_client()
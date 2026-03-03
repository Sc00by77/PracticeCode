"""
Simple TCP Chat Server
----------------------
Simulates a messaging server that multiple clients can connect to.
Each message from any client is broadcast to all connected clients.

Real-world use: Similar to Slack, Discord, WhatsApp servers
"""

import socket
import threading

# Configuration
SERVER_IP = "127.0.0.1"  # Localhost
SERVER_PORT = 5500
MAX_CLIENTS = 5  # Maximum number of simultaneous clients

# Store all connected clients
connected_clients = []
client_names = {}  # Store client names

def broadcast_message(message, sender_socket=None):
    """
    Send a message to all connected clients except the sender.
    """
    for client in connected_clients:
        if client != sender_socket:  # Don't send back to sender
            try:
                client.send(message.encode('utf-8'))
            except:
                # If sending fails, client probably disconnected
                connected_clients.remove(client)

def handle_client(client_socket, client_address):
    """
    Handle communication with a single client.
    This runs in a separate thread for each client.
    """
    print(f"[NEW CONNECTION] {client_address} connected")
    
    # Ask for client's name
    client_socket.send("Enter your name: ".encode('utf-8'))
    
    try:
        # Receive client's name
        client_name = client_socket.recv(1024).decode('utf-8').strip()
        client_names[client_socket] = client_name
        
        # Announce new user to everyone
        welcome_msg = f"\n {client_name} joined the chat!\n"
        print(f"[JOIN] {client_name} ({client_address[0]})")
        broadcast_message(welcome_msg, client_socket)
        
        # Send welcome message to the new user
        client_socket.send(f"\nWelcome {client_name}! Type 'quit' to exit.\n".encode('utf-8'))
        
        # Main message loop
        while True:
            # Receive message from client
            # recv() blocks until data arrives
            message = client_socket.recv(1024).decode('utf-8')
            
            if not message or message.strip().lower() == 'quit':
                # Client wants to disconnect
                break
            
            # Format and broadcast the message
            formatted_msg = f"{client_name}: {message}"
            print(f"[MESSAGE] {formatted_msg.strip()}")
            broadcast_message(formatted_msg, client_socket)
    
    except ConnectionResetError:
        print(f"[ERROR] {client_address} disconnected unexpectedly")
    
    except Exception as e:
        print(f"[ERROR] {client_address}: {e}")
    
    finally:
        # Client disconnected - clean up
        if client_socket in connected_clients:
            connected_clients.remove(client_socket)
        
        client_name = client_names.get(client_socket, "Unknown")
        
        # Announce departure
        goodbye_msg = f"\n {client_name} left the chat.\n"
        print(f"[DISCONNECT] {client_name} ({client_address[0]})")
        broadcast_message(goodbye_msg)
        
        # Clean up
        if client_socket in client_names:
            del client_names[client_socket]
        
        client_socket.close()

# Main server code
def start_server():
    """
    Start the TCP chat server.
    """
    # Step 1: Create TCP socket
    # AF_INET = IPv4, SOCK_STREAM = TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Step 2: Allow socket reuse (helpful for quick restarts)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Step 3: Bind socket to address and port
    server_socket.bind((SERVER_IP, SERVER_PORT))
    
    # Step 4: Start listening for connections
    # Backlog of 5 means up to 5 clients can wait in queue
    server_socket.listen(MAX_CLIENTS)
    
    print("=" * 60)
    print(" TCP Chat Server Started")
    print("=" * 60)
    print(f"✓ Listening on {SERVER_IP}:{SERVER_PORT}")
    print(f"✓ Maximum clients: {MAX_CLIENTS}")
    print(f"✓ Waiting for connections...\n")
    
    try:
        while True:
            # Step 5: Accept incoming connection
            # This blocks until a client connects
            client_socket, client_address = server_socket.accept()
            
            # Add client to our list
            connected_clients.append(client_socket)
            
            # Create a new thread to handle this client
            # This allows multiple clients to connect simultaneously
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address)
            )
            client_thread.daemon = True  # Thread dies when main program exits
            client_thread.start()
            
            # Show active connections
            print(f"[ACTIVE CONNECTIONS] {len(connected_clients)} client(s) connected\n")
    
    except KeyboardInterrupt:
        print("\n\n Server shutting down...")
    
    finally:
        # Close all client connections
        for client in connected_clients:
            client.close()
        
        # Close server socket
        server_socket.close()
        print("✓ Server stopped\n")

# Run the server
if __name__ == "__main__":
    start_server()
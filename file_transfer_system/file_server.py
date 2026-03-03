"""
Simple TCP File Transfer Server
--------------------------------
Receives files from clients and saves them to disk.

Real-world use: Similar to FTP servers, file upload services
"""

import socket
import os

# Configuration
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5600
BUFFER_SIZE = 4096  # Receive 4KB at a time
UPLOAD_FOLDER = "received_files"

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f" Created upload folder: {UPLOAD_FOLDER}")

def receive_file(client_socket, client_address):
    """
    Receive a file from a client.
    """
    try:
        # Step 1: Receive filename (first message)
        filename = client_socket.recv(1024).decode('utf-8')
        print(f"\n Receiving file: {filename}")
        print(f"   From: {client_address[0]}:{client_address[1]}")
        
        # Step 2: Send acknowledgment
        client_socket.send("READY".encode('utf-8'))
        
        # Step 3: Receive file size
        filesize = int(client_socket.recv(1024).decode('utf-8'))
        print(f"   Size: {filesize:,} bytes ({filesize/1024:.2f} KB)")
        
        # Step 4: Send acknowledgment
        client_socket.send("READY".encode('utf-8'))
        
        # Step 5: Receive the file data
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        bytes_received = 0
        
        # Open file for writing in binary mode
        with open(filepath, 'wb') as file:
            print(f"   Receiving data...", end='', flush=True)
            
            while bytes_received < filesize:
                # Receive chunk of data
                # This handles large files by receiving in pieces
                bytes_to_read = min(BUFFER_SIZE, filesize - bytes_received)
                chunk = client_socket.recv(bytes_to_read)
                
                if not chunk:
                    break  # Connection closed
                
                file.write(chunk)
                bytes_received += len(chunk)
                
                # Show progress every 100KB
                if bytes_received % 102400 == 0:
                    progress = (bytes_received / filesize) * 100
                    print(f"\r   Progress: {progress:.1f}%", end='', flush=True)
        
        print(f"\r   Progress: 100.0%")
        
        # Step 6: Send success confirmation
        if bytes_received == filesize:
            client_socket.send("SUCCESS".encode('utf-8'))
            print(f" File saved: {filepath}")
            print(f" Transfer complete: {bytes_received:,} bytes\n")
        else:
            client_socket.send("ERROR".encode('utf-8'))
            print(f" Transfer incomplete: received {bytes_received}/{filesize} bytes\n")
    
    except Exception as e:
        print(f" Error receiving file: {e}\n")
        try:
            client_socket.send("ERROR".encode('utf-8'))
        except:
            pass

def start_server():
    """
    Start the file transfer server.
    """
    # Create TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind and listen
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(5)
    
    print("=" * 60)
    print(" TCP File Transfer Server")
    print("=" * 60)
    print(f"✓ Listening on {SERVER_IP}:{SERVER_PORT}")
    print(f"✓ Upload folder: {UPLOAD_FOLDER}")
    print(f"✓ Waiting for file transfers...\n")
    
    try:
        while True:
            # Accept client connection
            client_socket, client_address = server_socket.accept()
            print(f"[CONNECTION] {client_address[0]}:{client_address[1]} connected")
            
            # Receive the file
            receive_file(client_socket, client_address)
            
            # Close connection
            client_socket.close()
            print(f"[DISCONNECT] {client_address[0]}:{client_address[1]}\n")
    
    except KeyboardInterrupt:
        print("\n\n Server shutting down...")
    
    finally:
        server_socket.close()
        print(" Server stopped\n")

# Run the server
if __name__ == "__main__":
    start_server()
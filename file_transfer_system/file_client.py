"""
Simple TCP File Transfer Client
--------------------------------
Sends files to the file transfer server.

Real-world use: Similar to FTP clients, file upload tools
"""

import socket
import os
import sys

# Configuration
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5600
BUFFER_SIZE = 4096  # Send 4KB at a time

def send_file(filepath):
    """
    Send a file to the server.
    """
    # Check if file exists
    if not os.path.exists(filepath):
        print(f" File not found: {filepath}")
        return
    
    # Get file information
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    
    print("=" * 60)
    print(" TCP File Transfer Client")
    print("=" * 60)
    print(f"File: {filename}")
    print(f"Size: {filesize:,} bytes ({filesize/1024:.2f} KB)")
    print(f"Target: {SERVER_IP}:{SERVER_PORT}\n")
    
    # Create TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Step 1: Connect to server
        print(f" Connecting to server...")
        client_socket.connect((SERVER_IP, SERVER_PORT))
        print(f" Connected!\n")
        
        # Step 2: Send filename
        print(f" Sending filename...")
        client_socket.send(filename.encode('utf-8'))
        
        # Wait for acknowledgment
        response = client_socket.recv(1024).decode('utf-8')
        if response != "READY":
            print(f" Server not ready")
            return
        
        # Step 3: Send file size
        print(f" Sending file size...")
        client_socket.send(str(filesize).encode('utf-8'))
        
        # Wait for acknowledgment
        response = client_socket.recv(1024).decode('utf-8')
        if response != "READY":
            print(f" Server not ready")
            return
        
        # Step 4: Send file data
        print(f" Transferring file data...")
        
        bytes_sent = 0
        
        # Open file in binary read mode
        with open(filepath, 'rb') as file:
            while bytes_sent < filesize:
                # Read chunk from file
                chunk = file.read(BUFFER_SIZE)
                
                if not chunk:
                    break
                
                # Send chunk to server
                # Note: send() might not send all data at once!
                # In production, you'd loop until all sent
                client_socket.sendall(chunk)
                
                bytes_sent += len(chunk)
                
                # Show progress
                progress = (bytes_sent / filesize) * 100
                print(f"\rProgress: {progress:.1f}%", end='', flush=True)
        
        print(f"\rProgress: 100.0%")
        print(f" Sent {bytes_sent:,} bytes\n")
        
        # Step 5: Receive confirmation
        print(f" Waiting for server confirmation...")
        response = client_socket.recv(1024).decode('utf-8')
        
        if response == "SUCCESS":
            print(f" Transfer successful!")
            print(f" File received by server\n")
        else:
            print(f" Transfer failed")
            print(f"   Server response: {response}\n")
    
    except ConnectionRefusedError:
        print(f" Could not connect to server at {SERVER_IP}:{SERVER_PORT}")
        print("   Make sure the server is running!\n")
    
    except Exception as e:
        print(f" Error: {e}\n")
    
    finally:
        client_socket.close()

# Main program
if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python file_client.py <filepath>")
        print("Example: python file_client.py document.txt")
        sys.exit(1)
    
    filepath = sys.argv[1]
    send_file(filepath)
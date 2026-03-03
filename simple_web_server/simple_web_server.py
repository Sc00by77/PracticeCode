"""
Simple Web Server - Lab 3
--------------------------
A basic HTTP web server built using TCP sockets.
Demonstrates how web servers work at the socket level.

This is similar to Apache, Nginx, or Python's built-in http.server,
but simplified to show the fundamentals.

Real-world use: Understanding how web servers handle HTTP over TCP
"""

import socket
import os
import mimetypes
from datetime import datetime

# Configuration
SERVER_HOST = '127.0.0.1'  # Localhost - only accessible from this computer
SERVER_PORT = 8080          # Port 8080 (common for development web servers)
WEB_ROOT = './www'          # Directory where web files are stored

# HTTP response templates
HTTP_200_HEADER = """HTTP/1.1 200 OK
Date: {date}
Server: SimpleWebServer/1.0
Content-Type: {content_type}
Content-Length: {content_length}
Connection: close

"""

HTTP_404_HEADER = """HTTP/1.1 404 Not Found
Date: {date}
Server: SimpleWebServer/1.0
Content-Type: text/html
Content-Length: {content_length}
Connection: close

"""

HTTP_404_BODY = """<!DOCTYPE html>
<html>
<head>
    <title>404 Not Found</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 100px auto;
            text-align: center;
        }}
        h1 {{ color: #d9534f; }}
    </style>
</head>
<body>
    <h1>404 - Page Not Found</h1>
    <p>The requested file <strong>{requested_path}</strong> was not found on this server.</p>
    <hr>
    <p><small>SimpleWebServer/1.0</small></p>
</body>
</html>
"""


def create_web_root():
    """
    Create the www directory if it doesn't exist.
    This is where we'll store our web files.
    """
    if not os.path.exists(WEB_ROOT):
        os.makedirs(WEB_ROOT)
        print(f"✓ Created web root directory: {WEB_ROOT}")


def create_sample_pages():
    """
    Create some sample HTML pages for testing.
    """
    # Create index.html (home page)
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Web Server - Home</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            font-size: 3em;
            margin-bottom: 20px;
        }
        p {
            font-size: 1.2em;
            line-height: 1.8;
        }
        a {
            color: #ffe066;
            text-decoration: none;
            font-weight: bold;
        }
        a:hover {
            text-decoration: underline;
        }
        .info-box {
            background: rgba(255, 255, 255, 0.2);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        ul {
            font-size: 1.1em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to Your Web Server!</h1>
        
        <div class="info-box">
            <h2>✓ It Works!</h2>
            <p>Congratulations! Your TCP-based web server is running successfully.</p>
        </div>

        <h3>What This Demonstrates:</h3>
        <ul>
            <li>TCP connection handling</li>
            <li>HTTP request parsing</li>
            <li>Serving HTML files</li>
            <li>Real-world socket programming</li>
        </ul>

        <h3>Try These Links:</h3>
        <ul>
            <li><a href="/">Home Page</a> (you are here)</li>
            <li><a href="/about.html">About Page</a></li>
            <li><a href="/contact.html">Contact Page</a></li>
            <li><a href="/notfound.html">Test 404 Error</a></li>
        </ul>

        <hr style="margin: 30px 0;">
        <p style="text-align: center;">
            <small>Powered by SimpleWebServer/1.0 | Built with Python TCP Sockets</small>
        </p>
    </div>
</body>
</html>
"""

    # Create about.html
    about_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>About - Simple Web Server</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f4f4f4;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 { color: #2a5298; }
        a { color: #2a5298; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .back-link {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: #2a5298;
            color: white;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>About This Web Server</h1>
        
        <h2>How It Works:</h2>
        <p>This web server is built from scratch using Python's socket library. Here's what happens when you request a page:</p>
        
        <ol>
            <li><strong>TCP Connection:</strong> Your browser establishes a TCP connection (3-way handshake)</li>
            <li><strong>HTTP Request:</strong> Browser sends GET request for the page</li>
            <li><strong>Server Processing:</strong> Server reads the file from disk</li>
            <li><strong>HTTP Response:</strong> Server sends headers and HTML content</li>
            <li><strong>Connection Close:</strong> TCP connection closes (4-way handshake)</li>
        </ol>

        <h2>Key Concepts:</h2>
        <ul>
            <li>Uses TCP (not UDP) for reliability</li>
            <li>Implements HTTP/1.1 protocol</li>
            <li>Handles multiple clients sequentially</li>
            <li>Serves static HTML files</li>
        </ul>

        <a href="/" class="back-link">← Back to Home</a>
    </div>
</body>
</html>
"""

    # Create contact.html
    contact_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Contact - Simple Web Server</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 15px;
        }
        h1 { color: #f5576c; }
        .info { 
            background: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        a { 
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background: #f5576c;
            color: white;
            text-decoration: none;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Contact Information</h1>
        
        <div class="info">
            <p><strong>Note:</strong> This is a demonstration server. Form submissions are not implemented in this basic version.</p>
        </div>

        <h2>Learning Resources:</h2>
        <ul>
            <li>Python Socket Documentation</li>
            <li>HTTP/1.1 Protocol (RFC 2616)</li>
            <li>TCP/IP Illustrated</li>
        </ul>

        <h2>Server Information:</h2>
        <p><strong>Server:</strong> SimpleWebServer/1.0</p>
        <p><strong>Protocol:</strong> HTTP/1.1 over TCP</p>
        <p><strong>Port:</strong> 8080</p>

        <a href="/">← Back to Home</a>
    </div>
</body>
</html>
"""

    # Write files to disk
    files = {
        'index.html': index_html,
        'about.html': about_html,
        'contact.html': contact_html
    }

    for filename, content in files.items():
        filepath = os.path.join(WEB_ROOT, filename)
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f" Created {filename}")


def get_file_content(requested_file):
    """
    Read and return the content of the requested file.
    
    Args:
        requested_file: Path to the requested file
        
    Returns:
        tuple: (file_content, content_type, success)
    """
    try:
        # Security: Prevent directory traversal attacks
        # Don't allow "../" in the path
        if ".." in requested_file:
            return None, "text/html", False

        # Construct full file path
        filepath = os.path.join(WEB_ROOT, requested_file.lstrip('/'))
        
        # If path is a directory, serve index.html
        if os.path.isdir(filepath):
            filepath = os.path.join(filepath, 'index.html')
        
        # Check if file exists
        if not os.path.exists(filepath):
            return None, "text/html", False
        
        # Determine content type based on file extension
        content_type, _ = mimetypes.guess_type(filepath)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Read file content
        # Use binary mode to handle images, PDFs, etc.
        with open(filepath, 'rb') as f:
            content = f.read()
        
        return content, content_type, True
        
    except Exception as e:
        print(f" Error reading file: {e}")
        return None, "text/html", False


def handle_client_request(client_socket, client_address):
    """
    Handle a single client request.
    
    This function:
    1. Receives the HTTP request
    2. Parses the requested file
    3. Sends appropriate HTTP response
    4. Closes the connection
    """
    try:
        # Step 1: Receive HTTP request from client
        # recv(4096) = receive up to 4096 bytes
        request_data = client_socket.recv(4096).decode('utf-8')
        
        # Check if we received data
        if not request_data:
            print(f" Empty request from {client_address[0]}")
            return
        
        # Step 2: Parse the HTTP request
        # HTTP request format: "GET /index.html HTTP/1.1\r\n..."
        request_lines = request_data.split('\r\n')
        
        # First line contains: METHOD PATH VERSION
        request_line = request_lines[0]
        print(f"\n Request from {client_address[0]}:{client_address[1]}")
        print(f"   {request_line}")
        
        # Parse the request line
        parts = request_line.split()
        if len(parts) < 2:
            print(f" Malformed request")
            return
        
        method = parts[0]  # GET, POST, etc.
        path = parts[1]     # /index.html, /about.html, etc.
        
        # We only handle GET requests in this simple server
        if method != 'GET':
            print(f" Unsupported method: {method}")
            return
        
        # Step 3: Get the requested file
        content, content_type, success = get_file_content(path)
        
        # Get current date for HTTP header
        current_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Step 4: Send HTTP response
        if success:
            # File found - send 200 OK response
            header = HTTP_200_HEADER.format(
                date=current_date,
                content_type=content_type,
                content_length=len(content)
            )
            
            # Send header (as bytes)
            client_socket.send(header.encode('utf-8'))
            
            # Send content (already in bytes)
            client_socket.send(content)
            
            print(f" Sent {path} ({len(content)} bytes, {content_type})")
            
        else:
            # File not found - send 404 response
            body = HTTP_404_BODY.format(requested_path=path)
            
            header = HTTP_404_HEADER.format(
                date=current_date,
                content_length=len(body)
            )
            
            # Send 404 response
            response = header + body
            client_socket.send(response.encode('utf-8'))
            
            print(f" 404 - File not found: {path}")
    
    except Exception as e:
        print(f" Error handling request: {e}")
    
    finally:
        # Step 5: Close the connection
        # Always close the socket when done
        client_socket.close()


def start_server():
    """
    Start the web server and listen for connections.
    """
    # Step 1: Create TCP socket
    # AF_INET = IPv4
    # SOCK_STREAM = TCP (stream-based, connection-oriented)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Step 2: Set socket options
    # SO_REUSEADDR allows reusing the address immediately after server stops
    # Without this, you'd have to wait ~60 seconds to restart server
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Step 3: Bind socket to address and port
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    
    # Step 4: Start listening for connections
    # The parameter (5) is the backlog - max number of queued connections
    server_socket.listen(5)
    
    print("=" * 70)
    print(" Simple Web Server Started!")
    print("=" * 70)
    print(f"✓ Server running on http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"✓ Serving files from: {os.path.abspath(WEB_ROOT)}")
    print(f"✓ Press Ctrl+C to stop the server")
    print("-" * 70)
    print("\n Open your web browser and visit:")
    print(f"   http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"   http://localhost:{SERVER_PORT}")
    print("\n Waiting for connections...\n")
    
    try:
        # Step 5: Main server loop - accept and handle connections
        while True:
            # accept() blocks until a client connects
            # Returns: (client_socket, client_address)
            client_socket, client_address = server_socket.accept()
            
            # Handle the client request
            # In a real web server, this would be in a separate thread
            # to handle multiple clients simultaneously
            handle_client_request(client_socket, client_address)
    
    except KeyboardInterrupt:
        print("\n\n Server stopped by user")
    
    finally:
        # Clean up
        server_socket.close()
        print(" Server socket closed")
        print("\nThank you for using Simple Web Server! 👋\n")


def main():
    """
    Main function - set up and start the server.
    """
    print("\n" + "=" * 70)
    print("Simple Web Server - Lab 3")
    print("=" * 70 + "\n")
    
    # Create web root directory
    create_web_root()
    
    # Create sample HTML pages
    create_sample_pages()
    
    print()
    
    # Start the server
    start_server()


if __name__ == "__main__":
    main()
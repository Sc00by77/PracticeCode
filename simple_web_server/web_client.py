"""
Simple Web Client
-----------------
A basic HTTP client that demonstrates how browsers make requests.
Shows the TCP connection and HTTP protocol in action.
"""

import socket

def fetch_page(host, port, path):
    """
    Fetch a web page using TCP sockets.
    
    Args:
        host: Server hostname or IP
        port: Server port number
        path: Path to request (e.g., "/index.html")
    """
    print("=" * 70)
    print(f"Fetching: http://{host}:{port}{path}")
    print("=" * 70)
    
    # Step 1: Create TCP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Step 2: Connect to server (initiates 3-way handshake)
        print(f"\n Connecting to {host}:{port}...")
        client_socket.connect((host, port))
        print(f" Connected! (TCP 3-way handshake complete)")
        
        # Step 3: Prepare HTTP GET request
        http_request = f"GET {path} HTTP/1.1\r\n"
        http_request += f"Host: {host}\r\n"
        http_request += "User-Agent: SimpleWebClient/1.0\r\n"
        http_request += "Accept: text/html\r\n"
        http_request += "Connection: close\r\n"
        http_request += "\r\n"  # Empty line marks end of headers
        
        print(f"\n Sending HTTP request:")
        print("-" * 70)
        print(http_request)
        print("-" * 70)
        
        # Step 4: Send the request
        client_socket.send(http_request.encode('utf-8'))
        
        # Step 5: Receive the response
        print(f"\n Receiving response...\n")
        
        response = b""
        while True:
            # Receive data in chunks
            chunk = client_socket.recv(4096)
            if not chunk:
                break  # No more data
            response += chunk
        
        # Step 6: Parse and display response
        response_text = response.decode('utf-8', errors='ignore')
        
        # Split headers and body
        parts = response_text.split('\r\n\r\n', 1)
        headers = parts[0]
        body = parts[1] if len(parts) > 1 else ""
        
        print("=" * 70)
        print("RESPONSE HEADERS:")
        print("=" * 70)
        print(headers)
        
        print("\n" + "=" * 70)
        print("RESPONSE BODY:")
        print("=" * 70)
        print(body[:500])  # Show first 500 characters
        if len(body) > 500:
            print(f"\n... ({len(body) - 500} more characters)")
        
        print("\n" + "=" * 70)
        print(f" Total response size: {len(response)} bytes")
        print("=" * 70)
        
    except ConnectionRefusedError:
        print(f"\n Connection refused. Is the server running on {host}:{port}?")
    except Exception as e:
        print(f"\n Error: {e}")
    finally:
        # Step 7: Close connection (initiates 4-way handshake)
        client_socket.close()
        print(f"\n Connection closed (TCP 4-way handshake complete)\n")


def main():
    """
    Test the web client by fetching pages from the server.
    """
    print("\n" + "=" * 70)
    print("Simple Web Client - Testing Tool")
    print("=" * 70 + "\n")
    
    # Make sure your web server is running first!
    
    # Test 1: Fetch home page
    fetch_page('127.0.0.1', 8080, '/')
    
    input("\nPress Enter to fetch about page...")
    
    # Test 2: Fetch about page
    fetch_page('127.0.0.1', 8080, '/about.html')
    
    input("\nPress Enter to test 404 error...")
    
    # Test 3: Test 404 error
    fetch_page('127.0.0.1', 8080, '/does-not-exist.html')


if __name__ == "__main__":
    main()
# Step 1: Open MULTIPLE terminal windows (at least 3)

# Terminal 1 - Start the chat server:
python chat_server.py

# You should see:
# ============================================================
#  TCP Chat Server Started
# ============================================================
# ✓ Listening on 127.0.0.1:5500
# ✓ Maximum clients: 5
# ✓ Waiting for connections...

# Terminal 2 - Start first chat client (Alice):
python chat_client.py
# When prompted, enter name: Alice
# Start chatting!

# Terminal 3 - Start second chat client (Bob):
python chat_client.py
# When prompted, enter name: Bob
# Start chatting!

# Terminal 4 (Optional) - Start third client (Charlie):
python chat_client.py
# When prompted, enter name: Charlie

# Now all clients can see each other's messages!
# Type 'quit' in any client to disconnect
# Press Ctrl+C in server terminal to stop server
```

### **Expected Output:**

**Server (Terminal 1):**
```
============================================================
 TCP Chat Server Started
============================================================
✓ Listening on 127.0.0.1:5500
✓ Maximum clients: 5
✓ Waiting for connections...

[NEW CONNECTION] ('127.0.0.1', 54321) connected
[JOIN] Alice (127.0.0.1)
[ACTIVE CONNECTIONS] 1 client(s) connected

[NEW CONNECTION] ('127.0.0.1', 54322) connected
[JOIN] Bob (127.0.0.1)
[ACTIVE CONNECTIONS] 2 client(s) connected

[MESSAGE] Alice: Hi everyone!
[MESSAGE] Bob: Hey Alice!
[MESSAGE] Alice: How are you?
[DISCONNECT] Bob (127.0.0.1)
[ACTIVE CONNECTIONS] 1 client(s) connected
```

**Client 1 - Alice (Terminal 2):**
```
============================================================
 TCP Chat Client
============================================================
 Connecting to 127.0.0.1:5500...
✓ Connected to server!

Enter your name: Alice

Welcome Alice! Type 'quit' to exit.

 Bob joined the chat!

Hi everyone!
Bob: Hey Alice!
How are you?

 Bob left the chat.
```

**Client 2 - Bob (Terminal 3):**
```
============================================================
💬 TCP Chat Client
============================================================
 Connecting to 127.0.0.1:5500...
✓ Connected to server!

Enter your name: Bob

Welcome Bob! Type 'quit' to exit.
Alice: Hi everyone!
Hey Alice!
Alice: How are you?
quit
 Goodbye!
✓ Disconnected
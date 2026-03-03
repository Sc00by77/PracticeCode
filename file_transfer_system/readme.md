# Step 1: Create a test file to transfer
echo "Hello, this is a test file!" > test.txt

# Or create a larger file:
# On Linux/Mac:
dd if=/dev/zero of=largefile.bin bs=1024 count=1024  # Creates 1MB file

# On Windows (PowerShell):
# fsutil file createnew largefile.bin 1048576  # Creates 1MB file

# Step 2: Open TWO terminal windows

# Terminal 1 - Start the file server:
python file_server.py

# You should see:
# ============================================================
#  TCP File Transfer Server
# ============================================================
# ✓ Listening on 127.0.0.1:5600
# ✓ Upload folder: received_files
# ✓ Waiting for file transfers...

# Terminal 2 - Send a file:
python file_client.py test.txt

# Or send the large file:
python file_client.py largefile.bin

# Check the 'received_files' folder - your file should be there!

# To stop server: Press Ctrl+C in Terminal 1
```

### **Expected Output:**

**Server (Terminal 1):**
```
============================================================
 TCP File Transfer Server
============================================================
✓ Created upload folder: received_files
✓ Listening on 127.0.0.1:5600
✓ Upload folder: received_files
✓ Waiting for file transfers...

[CONNECTION] 127.0.0.1:54567 connected

 Receiving file: test.txt
   From: 127.0.0.1:54567
   Size: 30 bytes (0.03 KB)
   Progress: 100.0%
✓ File saved: received_files/test.txt
✓ Transfer complete: 30 bytes

[DISCONNECT] 127.0.0.1:54567

[CONNECTION] 127.0.0.1:54568 connected

 Receiving file: largefile.bin
   From: 127.0.0.1:54568
   Size: 1,048,576 bytes (1024.00 KB)
   Progress: 100.0%
✓ File saved: received_files/largefile.bin
✓ Transfer complete: 1,048,576 bytes

[DISCONNECT] 127.0.0.1:54568
```

**Client (Terminal 2):**
```
============================================================
 TCP File Transfer Client
============================================================
File: test.txt
Size: 30 bytes (0.03 KB)
Target: 127.0.0.1:5600

📡 Connecting to server...
✓ Connected!

 Sending filename...
 Sending file size...
 Transferring file data...
Progress: 100.0%
✓ Sent 30 bytes

 Waiting for server confirmation...
✓ Transfer successful!
✓ File received by server
# Open terminal and run:
python simple_web_server.py
```

### **Step 3: You'll See This Output**
```
======================================================================
Simple Web Server - Lab 3
======================================================================

 Created web root directory: ./www
 Created index.html
 Created about.html
 Created contact.html

======================================================================
 Simple Web Server Started!
======================================================================
 Server running on http://127.0.0.1:8080
 Serving files from: /path/to/your/www
 Press Ctrl+C to stop the server
----------------------------------------------------------------------

 Open your web browser and visit:
   http://127.0.0.1:8080
   http://localhost:8080

 Waiting for connections...
```

### **Step 4: Open Your Web Browser**
```
Visit: http://localhost:8080
```

### **Step 5: You'll See Server Logs**
```
 Request from 127.0.0.1:54321
   GET / HTTP/1.1
 Sent /index.html (2847 bytes, text/html)

 Request from 127.0.0.1:54322
   GET /about.html HTTP/1.1
 Sent /about.html (1563 bytes, text/html)

 Request from 127.0.0.1:54323
   GET /notfound.html HTTP/1.1
 404 - File not found: /notfound.html




 python web_client.py
```

---

## **Expected Output: Server Terminal**
```
======================================================================
Simple Web Server - Lab 3
======================================================================

 Created web root directory: ./www
 Created index.html
 Created about.html
 Created contact.html

======================================================================
 Simple Web Server Started!
======================================================================
 Server running on http://127.0.0.1:8080
 Serving files from: /Users/student/www
 Press Ctrl+C to stop the server
----------------------------------------------------------------------

 Open your web browser and visit:
   http://127.0.0.1:8080
   http://localhost:8080

 Waiting for connections...


 Request from 127.0.0.1:54321
   GET / HTTP/1.1
 Sent /index.html (2847 bytes, text/html)

 Request from 127.0.0.1:54322
   GET /about.html HTTP/1.1
 Sent /about.html (1563 bytes, text/html)

 Request from 127.0.0.1:54323
   GET /contact.html HTTP/1.1
 Sent /contact.html (1234 bytes, text/html)

 Request from 127.0.0.1:54324
   GET /notfound.html HTTP/1.1
 404 - File not found: /notfound.html
import urllib.parse
import urllib.request

BOT_TOKEN = "8270536306:AAG6Q0rafcyeyoXYyyqKD_QcWffZODN88zY"
CHAT_ID = "8970532258"

message = """🚨 TEST PATIENT ALERT

Patient ID: P001
Status: NORMAL → WARNING
Risk Score: 0.28

This is a test notification from the Patient Vital Monitoring System.
"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

data = urllib.parse.urlencode({
    "chat_id": CHAT_ID,
    "text": message
}).encode()

request = urllib.request.Request(url, data=data, method="POST")

with urllib.request.urlopen(request) as response:
    print(response.read().decode())
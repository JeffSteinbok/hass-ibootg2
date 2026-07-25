"""
Example credentials file for Dataprobe DxP (iBoot) testing.
Copy this file to credentials.py and fill in your actual values.

credentials.py is gitignored and will NOT be committed.
"""

# Device connection details
HOST = "192.168.1.50"
PORT = 9100

# Device credentials (iBoot factory default is admin / admin[last3ofmac])
USERNAME = "admin"
PASSWORD = "your-password"

# Number of outlets/relays on the device (1 for iBoot / iBoot-G2)
NUM_RELAYS = 1

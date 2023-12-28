# IP Pinger

IP Pinger is a Python application that allows users to monitor multiple IP addresses. It sends ping requests to each IP address and displays their response times and TTL (Time To Live) values. The application is built with a Tkinter GUI, providing a user-friendly interface for managing IP addresses.

## Features

- Add and monitor multiple IP addresses.
- Display the ping response time and TTL for each IP address.
- Interactive GUI with options to increase/decrease font size.
- Load IP addresses from a text file.
- Save the last opened file path for quick access.
- Real-time updates of IP status.
- Context menu for easy access to common actions.

## Usage

To run the script, use a Python interpreter as shown below:

```bash
python pinger_app.py

### Adding an IP Address

1. Use the "Add IP" option in the Options menu.
2. Enter the Name and IP Address in the new window.
3. Click "Add IP" to add the IP to the monitoring list.

### Editing an IP Address

1. Double-click on an IP in the list.
2. Modify the Name or IP Address.

### Removing an IP Address

1. Right-click on an IP and select "Remove IP".

### Pinging an IP Address

1. Right-click on an IP and select "Ping This IP" to start monitoring the ping response.
2. Right-click and select "Stop Pinging This IP" to stop monitoring.

### Loading IPs from a File

1. Use the "Choose file" option in the Options menu.
2. Select a .txt file with IP addresses.

### Saving the Last Opened File Path

- The application automatically saves the path of the last opened file.

### Increasing/Decreasing Font Size

- Use the "+" and "-" options in the menu bar to adjust the font size.

## Dependencies

- Python 3.7 or later.
- Tkinter (usually comes with Python).
- Additional libraries: os, platform, subprocess, re, threading, asyncio, winreg.

## Limitations

- Currently, the application is tailored for Windows environments, but it can be modified for other operating systems.
- The application does not support IPv6 addresses yet.

## Contributing

Contributions to improve IP Pinger are welcome. Please feel free to fork the repository and submit pull requests.

## License

IP Pinger is released under the MIT License.
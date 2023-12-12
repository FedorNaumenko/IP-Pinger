import os
import platform
import subprocess
import tkinter as tk
from tkinter import ttk
import re
import threading
from tkinter import filedialog
import winreg

class PingerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IP Pinger")
        self.root.configure(bg="lightgrey")  # Set the background color of the window to light grey
        self.root.geometry("450x500")  # Set the size of the window
        self.pinging_ips = set()

        # Create a frame to hold the treeview
        self.tree_frame = tk.Frame(root, bg="lightgrey")
        self.tree_frame.pack(fill=tk.BOTH, expand=True)  # Make the frame expandable

        # Create the Treeview inside the tree_frame
        self.tree = ttk.Treeview(self.tree_frame, columns=('Name','IP', 'Time', 'TTL'), show='headings')
        self.tree.heading('Name', text='Name')
        self.tree.heading('IP', text='IP')
        self.tree.heading('Time', text='Time')
        self.tree.heading('TTL', text='TTL')
        self.tree.column('Name', width=100)
        self.tree.column('IP', width=100)
        self.tree.column('Time', width=100)
        self.tree.column('TTL', width=100)
        
        self.tree.heading('Name', text='Name', command=lambda: self.sort_column('Name', False))
        self.tree.heading('IP', text='IP', command=lambda: self.sort_column('IP', False))

        # Create a vertical scrollbar
        scrollbar = ttk.Scrollbar(self.tree_frame, orient='vertical', command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')

        # Associate the scrollbar with the treeview
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill=tk.BOTH, expand=True)  # Make the treeview expandable
        
        # Create a menu bar
        menu_bar = tk.Menu(root)

        # Create a menu item
        options_menu = tk.Menu(menu_bar, tearoff=0)

        # Add commands to the menu item
        options_menu.add_command(label="Add IP", command=self.add_ip)
        options_menu.add_command(label="Choose file", command=self.load_ips_from_file)

        # Add the menu item to the menu bar
        menu_bar.add_cascade(label="Options", menu=options_menu)

        # Set the menu bar
        root.config(menu=menu_bar)

        # Create a right-click context menu
        context_menu = tk.Menu(root, tearoff=0)

        # Add commands to the context menu
        context_menu.add_command(label="Remove IP", command=self.remove_ip)
        context_menu.add_command(label="Ping This IP", command=self.ping_selected_ip)
        context_menu.add_command(label="Stop Pinging This IP", command=self.stop_pinging_selected_ip)
        context_menu.add_command(label="Connect To This IP", command=self.connect_to_selected_ip)

        def show_context_menu(event):
            # Show the context menu at the position of the mouse cursor
            context_menu.post(event.x_root, event.y_root)

        # Bind the context menu to the right mouse button of the treeview
        self.tree.bind('<Button-3>', show_context_menu)

        # Try to load the last opened file path from the registry
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\MyApp') as key:
                self.last_opened_file_path = winreg.QueryValueEx(key, 'LastOpenedFilePath')[0]
        except FileNotFoundError:
            self.last_opened_file_path = None

        # If the last opened file path exists, load the IPs from it
        if self.last_opened_file_path and os.path.exists(self.last_opened_file_path):
            self.load_ips_from_file(self.last_opened_file_path)

    def load_ips_from_file(self, file_path=None):
         # If a file path was not provided
        if file_path is None:
            # Open a file dialog and get the selected file's path
            file_path = filedialog.askopenfilename(filetypes=[('Text Files', '*.txt')])

        # If a file was selected
        if file_path:
            # Initialize the last opened file path to None
            self.last_opened_file_path = file_path   

            # Save the path of the opened file to the registry
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\MyApp') as key:
                winreg.SetValueEx(key, 'LastOpenedFilePath', 0, winreg.REG_SZ, file_path)

            # Open the file and load the names and IPs
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                self.ip_addresses = []
                for i in range(0, len(lines), 2):
                    name = lines[i].strip()
                    ip = lines[i + 1].strip() if i + 1 < len(lines) else ''
                    self.ip_addresses.append((name, ip))
                    #print(f"Name: {name}, IP: {ip}")  # Debugging line

            # Clear the treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Add the names and IPs to the treeview
            for name, ip in self.ip_addresses:
                item = self.tree.insert('', 'end', values=(name, ip, '', ''))
                self.pinging_ips.add(ip)
                self.ping_ip_in_background(ip, item)

    def add_ip(self):
        # Create a new window
        new_window = tk.Toplevel(self.root)

        # Create labels and entries in the new window
        label_name = tk.Label(new_window, text="Enter Name")
        label_name.pack(padx=10, pady=10)

        name_entry = tk.Entry(new_window)
        name_entry.pack(padx=10, pady=10)

        label_ip = tk.Label(new_window, text="Enter IP Address")
        label_ip.pack(padx=10, pady=10)

        ip_entry = tk.Entry(new_window)
        ip_entry.pack(padx=10, pady=10)

        # Create a button that adds the entered name and IP address to the treeview and closes the window
        add_button = tk.Button(new_window, text="Add IP", command=lambda: self.add_ip_to_tree(name_entry.get(), ip_entry.get(), new_window))
        add_button.pack(padx=10, pady=10)

    def add_ip_to_tree(self, name, ip, window):
        # Add the name and IP address to the treeview
        self.tree.insert('', 'end', values=(name, ip, '', ''))

        # Write the IP to a file
        with open(self.last_opened_file_path, 'a', encoding='utf-8') as f:
            f.write(f'{name}\n{ip}\n')

        # Close the window
        window.destroy()

    def remove_ip(self):
        selected_item = self.tree.selection()[0]
        self.tree.delete(selected_item)

    def ping_ip(self, ip):
        param = '-n' if platform.system().lower()=='windows' else '-c'
        command = ['ping', param, '1', ip]
        try:
            output = subprocess.check_output(command, timeout=1, creationflags=subprocess.CREATE_NO_WINDOW).decode()
            time_match = re.search(r"Average = (\d+ms)", output)
            ttl_match = re.search(r"TTL=(\d+)", output)
            time = time_match.group(1) if time_match else ''
            ttl = ttl_match.group(1) if ttl_match else ''
            return True, time, ttl
        except subprocess.CalledProcessError:
            print(f"Failed to execute the 'ping' command for {ip}.")
        except subprocess.TimeoutExpired:
            print(f"Timeout expired while pinging {ip}.")
        except Exception as e:
            print(f"An unexpected error occurred while pinging {ip}: {e}")
        return False, '', ''

    def ping_selected_ip(self):
        # Get the selected IP address
        selected_item = self.tree.selection()[0]
        ip = self.tree.item(selected_item)['values'][0]

        # Start a new thread that runs the ping operation
        threading.Thread(target=self.ping_ip_in_background, args=(ip, selected_item)).start()

    def ping_ip_in_background(self, ip, item):
        # Define a target function to be run in a new thread
        def target():
            try:
                # Try to ping the IP address
                result, time, ttl = self.ping_ip(ip)
            except Exception as e:
                # If an error occurs, set the result, time, and ttl to default values
                result, time, ttl = False, '', ''
            # If the IP address is not in the list of pinging IPs or the item no longer exists, return
            if ip not in self.pinging_ips or not self.tree.exists(item):
                return
            # If the ping was successful, tag the tree item with 'ping_success' and set its background to green
            if result:
                self.tree.item(item, tags=('ping_success',))
                self.tree.tag_configure('ping_success', background='green3')
            # If the ping was not successful, tag the tree item with 'ping_fail' and set its background to red
            else:
                self.tree.item(item, tags=('ping_fail',))
                self.tree.tag_configure('ping_fail', background='firebrick1')
            # Get the current values of the tree item
            values = self.tree.item(item)['values']
            # Update the name, time, and ttl of the tree item
            values[2] = time
            values[3] = ttl
            # Update the tree item with the new values
            self.tree.item(item, values=values)
            # Schedule the target function to be run again after 1 second
            self.root.after(5000, target)
        # Start a new thread that runs the target function
        threading.Thread(target=target).start()

    def stop_pinging_selected_ip(self):
        # Get the first selected item in the treeview
        selected_item = self.tree.selection()[0]
        
        # Get the IP address of the selected item
        ip = self.tree.item(selected_item)['values'][0]
        
        # Remove the IP address from the set of pinging IPs
        self.pinging_ips.discard(ip)
        
        # Tag the selected item with 'ping_stop'
        self.tree.item(selected_item, tags=('ping_stop',))
        
        # Configure the 'ping_stop' tag to have a white background
        self.tree.tag_configure('ping_stop', background='white')
        
        # Update the selected item's values to show that it's no longer being pinged
        self.tree.item(selected_item, values=(ip, '', ''))

    def connect_to_selected_ip(self):
        # Get the first selected item in the treeview
        selected_item = self.tree.selection()[0]
        
        # Get the IP address of the selected item
        ip = self.tree.item(selected_item)['values'][1]
        
        # Create the command to establish an RDP connection
        command = ['mstsc', '-v:{}'.format(ip)]
        
        # Execute the command in a new process
        subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)

    def sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        l.sort(reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        # reverse sort next time
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

# Create a root window
root = tk.Tk()

# Create an instance of MyApp
app = PingerApp(root)

# Start the main loop
root.mainloop()

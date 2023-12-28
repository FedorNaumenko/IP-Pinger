import os
import platform
import subprocess
import tkinter as tk
from tkinter import ttk
import re
import threading
from tkinter import filedialog
import winreg
import tkinter.simpledialog as simpledialog
import asyncio

class PingerApp():
    def __init__(self, root):
        self.root = root
        self.root.title("IP Pinger")
        self.root.configure(bg="lightgrey")  # Set the background color of the window to light grey
        self.root.geometry("450x500")  # Set the size of the window
        self.pinging_ips = set()
        # Create a style
        self.style = ttk.Style()
        self.style.configure("Treeview", font=("TkDefaultFont", 12))
        self.font_size = 12
        
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
        
        # Create a right-click context menu
        context_menu = tk.Menu(root, tearoff=0)

        # Add commands to the context menu
        context_menu.add_command(label="Ping This IP", command=self.ping_selected_ip)
        context_menu.add_command(label="Stop Pinging This IP", command=self.stop_pinging_selected_ip)
        context_menu.add_command(label="Edit Name", command=self.edit_name)
        context_menu.add_command(label="Remove IP", command=self.remove_ip)

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

        # Bind the double click event to the edit_name function
        self.tree.bind('<Double-1>', self.connect_to_selected_ip)

        # Create a menu bar
        self.create_menu_bar()

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def do_nothing(self):
        pass

    def increase_font_size(self):
        self.font_size += 1
        self.style.configure("Treeview", font=("TkDefaultFont", self.font_size))
        self.create_menu_bar()  # Call create_menu_bar to update the menu bar
            
    def decrease_font_size(self):
        if self.font_size > 1:
            self.font_size -= 1
        self.style.configure("Treeview", font=("TkDefaultFont", self.font_size))
        self.create_menu_bar()  # Call create_menu_bar to update the menu bar

    def create_menu_bar(self):
         # Create a menu bar
        self.menu_bar = tk.Menu(self.root)

        # Create a menu item
        options_menu = tk.Menu(self.menu_bar, tearoff=0)

        # Add commands to the menu item
        options_menu.add_command(label="Add IP", command=self.add_ip)
        options_menu.add_command(label="Choose file", command=self.load_ips_from_file)

        # Add the menu item to the menu bar
        self.menu_bar.add_cascade(label="Options", menu=options_menu)

        # Set the menu bar
        self.root.config(menu=self.menu_bar)

        self.menu_bar.add_command(label="+", command=self.increase_font_size)
        self.menu_bar.add_command(label="Font Size: {}".format(self.font_size), command=self.do_nothing)
        self.menu_bar.add_command(label="-", command=self.decrease_font_size)

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
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
                self.ip_addresses = []
                for i in range(0, len(lines), 2):
                    name = lines[i].strip()
                    ip = lines[i + 1].strip() if i + 1 < len(lines) else ''
                    self.ip_addresses.append((name, ip))

            # Clear the treeview
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Add the names and IPs to the treeview
            for name, ip in self.ip_addresses:
                item = self.tree.insert('', 'end', values=(name, ip, '', ''))
                self.pinging_ips.add(ip)  # Add the IP address to the set of pinging IPs
                # Run the pinging function in a separate thread
                threading.Thread(target=asyncio.run, args=(self.ping_ip_in_background(ip, item),)).start()

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
        with open(self.last_opened_file_path, 'a', encoding='utf-8', errors='ignore') as f:
            f.write(f'\n{name}\n{ip}')
            
        # Close the window
        window.destroy()

    def remove_ip(self):
        selected_item = self.tree.selection()[0]
        ip = str(self.tree.item(selected_item)['values'][1])  # Get the IP of the selected item
        name = str(self.tree.item(selected_item)['values'][0])  # Get the name of the selected item

        # Open the file and read all lines
        with open(self.last_opened_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()

        # Remove the lines containing the IP and name
        lines = [line for line in lines if ip not in line and name not in line]
       
        # Write the remaining lines back to the file
        with open(self.last_opened_file_path, 'w', encoding='utf-8', errors='ignore') as file:
            for line in lines:
                file.write(line)

        self.tree.delete(selected_item)

    async def ping_ip(self, ip):
        param = '-n' if platform.system().lower()=='windows' else '-c'
        command = ['ping', param, '1', ip]
        process = None

        # Setup for Windows to prevent opening a new window
        if platform.system().lower() == 'windows':
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
        else:
            si = None

        try:
            process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW, startupinfo=si)
            stdout, _ = await process.communicate()
            if stdout:
                output = stdout.decode()
                time_match = re.search(r"Average = (\d+ms)", output)
                ttl_match = re.search(r"TTL=(\d+)", output)
                time = time_match.group(1) if time_match else ''
                ttl = ttl_match.group(1) if ttl_match else ''
                if output.find('Request timed out') != -1:
                    return False, '', ''
                return True, time, ttl
            else:
                return False, '', ''
        except Exception as e:
            print(f"An unexpected error occurred while pinging {ip}: {e}")
            return False, '', ''

    async def ping_ip_in_background(self, ip, item):
        while True:
            try:
                result, time, ttl = await self.ping_ip(ip)
            except Exception as e:
                result, time, ttl = False, '', ''

            if ip not in self.pinging_ips: #or not self.tree.exists(item):
                return
            values = self.tree.item(item)['values']
            while len(values) < 4:
                values.append(None)
            values[2] = time
            values[3] = ttl
            self.tree.item(item, values=values)
            if result:
                self.tree.item(item, tags=('ping_success',))
                self.tree.tag_configure('ping_success', background='green3')
            elif self.tree.item(item)['tags'] == ('ping_stop',):
                self.tree.item(item, tags=('ping_stop',))
                self.tree.tag_configure('ping_stop', background='white')
            elif not result and 'ping_stop' not in self.tree.item(item)['tags']:
                self.tree.item(item, tags=('ping_fail',))
                self.tree.tag_configure('ping_fail', background='firebrick1')
        
            await asyncio.sleep(3)
        
    def ping_selected_ip(self):
        # Get the selected IP address
        selected_item = self.tree.selection()[0]
        ip = self.tree.item(selected_item)['values'][1]
        
        # Add the IP address to the set of pinging IPs
        self.pinging_ips.add(ip)
        print(f"Added {ip} to pinging IPs: {self.pinging_ips}")

        self.tree.item(selected_item, tags=('ping',))

        # Configure the 'ping' tag to have a green background
        self.tree.tag_configure('ping', background='green3')

        # Run the ping operation
        #asyncio.run_coroutine_threadsafe(self.ping_ip_in_background(ip, selected_item), self.loop)

    def stop_pinging_selected_ip(self):
        # Get the first selected item in the treeview
        selected_item = self.tree.selection()[0]
        
        # Get the IP address of the selected item
        ip = self.tree.item(selected_item)['values'][1]
        name = self.tree.item(selected_item)['values'][0]

        # Remove the IP address from the set of pinging IPs
        self.pinging_ips.discard(ip)
        print(f"Removed {ip} from pinging IPs: {self.pinging_ips}")

        # Tag the selected item with 'ping_stop'
        self.tree.item(selected_item, tags=('ping_stop',))
        
        # Configure the 'ping_stop' tag to have a white background
        self.tree.tag_configure('ping_stop', background='white')
        
        # Update the selected item's values to show that it's no longer being pinged
        self.tree.item(selected_item, values=(name, ip, '', ''))
        
    def connect_to_selected_ip(self, event=None):
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

    def edit_name(self):
        # Get the selected item
        selected_item = self.tree.selection()[0]

        # Get the current name
        current_name = self.tree.item(selected_item)['values'][0]

        # Open a dialog to enter the new name
        new_name = simpledialog.askstring("Input", "Enter new name",
                                        initialvalue=current_name)

        # If a new name was entered, update the name
        if new_name is not None:
            old_name = self.tree.item(selected_item)['values'][0]
            self.tree.item(selected_item, values=(new_name, self.tree.item(selected_item)['values'][1]))
            
            # Replace the name in the file
            self.replace_name_in_file(old_name, new_name, self.last_opened_file_path)
            
    def replace_name_in_file(self, old_name, new_name, filename):
        # Open the file and read all lines
        with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()

        # Replace the name in the appropriate line
        for i, line in enumerate(lines):
            parts = line.split()  # Split the line into parts
            for j, part in enumerate(parts):
                if part == old_name:  # Only replace the part that exactly matches the old name
                    parts[j] = new_name
            lines[i] = ' '.join(parts)  # Join the parts back together

        # Write all lines back to the file
        with open(filename, 'w', encoding='utf-8', errors='ignore') as file:
            for i, line in enumerate(lines):
                if i < len(lines) - 1:
                    file.write(line + '\n')
                else:
                    file.write(line)

def main():
    # Create a root window
    root = tk.Tk()

    # Create an instance of MyApp
    app = PingerApp(root)

    # Start the main loop
    root.mainloop()

if __name__ == '__main__':
    main()
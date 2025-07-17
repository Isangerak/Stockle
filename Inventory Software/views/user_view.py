import tkinter as tk
from tkinter import ttk
from tkinter import messagebox



#------------------------Parent Classes------------------------------#

class User_Form(tk.Frame):
    # Form used for user additions / deletions
    def __init__(self,master):
        super().__init__(master)
        ttk.Label(self, text="Username").grid(row=1, column=0, pady=5)
        self.username_entry = ttk.Entry(self)
        self.username_entry.grid(row=1, column=1, pady=5)
        ttk.Label(self, text="Description").grid(row=2, column=0, pady=5)
        self.description_entry = ttk.Entry(self)
        self.description_entry.grid(row=2, column=1, pady=5)
        self.save_button = ttk.Button(self, text="Save")
         # Permissions selection 
        self.permissions_label = ttk.Label(self, text="Select Permissions").grid(row=6, column=0, pady=5)
        self.permissions_options = {"Read (R)": "R", "Write (W)": "W", "Execute (X)": "X"}
        self.permissions_vars = {key: tk.BooleanVar() for key in self.permissions_options}
        
        self.permissions_checkbuttons = []
        for i, (label, value) in enumerate(self.permissions_options.items()):
            chk = ttk.Checkbutton(self, text=label, variable=self.permissions_vars[label], command=self.__update_permissions)
            chk.grid(row=7 + i, column=1, sticky="w")
            self.permissions_checkbuttons.append((chk, value))
        
        
    def __update_permissions(self):
        # Set all permissions under chosen permission level as well
        if self.permissions_vars["Execute (X)"].get():
            self.permissions_vars["Write (W)"].set(True)
            self.permissions_vars["Read (R)"].set(True)
        elif self.permissions_vars["Write (W)"].get():
            self.permissions_vars["Read (R)"].set(True)
        
        # Prevent unchecking lower levels while higher levels are selected
        if not self.permissions_vars["Read (R)"].get():
            self.permissions_vars["Write (W)"].set(False)
            self.permissions_vars["Execute (X)"].set(False)
        elif not self.permissions_vars["Write (W)"].get():
            self.permissions_vars["Execute (X)"].set(False)



class EntryWindow(tk.Tk):
    # General submission Window, inherited by login frame and changequantity frames
    def __init__(self):
        tk.Tk.__init__(self)
        # Page Layout
        # Field 1 
        self.label1 = ttk.Label(self)
        self.label1.grid(row=0, column=0, padx=10, pady=10)
        self.entry1 = ttk.Entry(self)
        self.entry1.grid(row=0, column=1, padx=10, pady=10)
        # Field 2
        self.label2 = ttk.Label(self)
        self.label2.grid(row=1, column=0, padx=10, pady=10)
        self.entry2 = ttk.Entry(self, show="*")
        self.entry2.grid(row=1, column=1, padx=10, pady=10)

        # Button
        self.submit_button = ttk.Button(self, text="Submit")
        self.submit_button.grid(row=2, columnspan=2, pady=10)

        self.entry1.focus()


#------------------------Container Frames------------------------------#
class Edit_form(User_Form):
    def __init__(self,master,user):
        super().__init__(master)
        # Update user form details with current ones
        self.username_entry.insert(0,user['username'])
        self.description_entry.insert(0,user['description'])
        self.save_button.grid(row=10, column=0, columnspan=2, pady=10)




class ShowUsersFrame(tk.Frame):
    def __init__(self, parent, controller):
        # Frame to show all users
        super().__init__(parent)
        self.__controller = controller
        self.__users = self.__controller.get_users()
        # Config
        title_frame = tk.Frame(self)
        title_frame.pack(fill="x", pady=10)

        self.__label = ttk.Label(title_frame, text="All Users", font=("Arial", 15))
        self.__label.pack(side="left")

        # Frame for Buttons
        self.__button_frame = tk.Frame(title_frame)
        self.__button_frame.pack(side="right")
        # Buttons for adding and deleting users
        add_button = ttk.Button(self.__button_frame, text="Add User", command=lambda: self.__controller.app_controller.show_user_frame("Add User"))
        add_button.pack(side="left", padx=(0, 5))
        
        delete_button = ttk.Button(self.__button_frame, text="Delete User", command=self.__enter_delete_mode)
        delete_button.pack(side="right", padx=(0, 5))

        self.__exit_button = ttk.Button(self.__button_frame, text="Exit Delete Mode", command=self.__exit_delete_mode)
        self.__exit_button.pack(side="right", padx=(0, 5))
        self.__exit_button.pack_forget()  # Hide initially
        # Create list for users
        self.__users_list = tk.Listbox(self)
        self.__users_list.pack(fill="both", expand=True)
        self.__users_list.delete(0, tk.END)

        # add double click feature
        self.__users_list.bind('<Double-1>', self.__get_user)
        for user in self.__users:
            self.__users_list.insert(tk.END, f"{user['username']}: {user['description']} : {user['permissions']}")

    def __enter_delete_mode(self):
        # A double click on a user will now ask if you wan to delete it
        self.__label.config(text="Delete User")
        self.__users_list.config(highlightthickness=2, highlightbackground="red")
        self.__users_list.bind('<Double-1>', self.__confirm_delete)
        self.__exit_button.pack(side="right", padx=(0, 5))  # Show the exit button

    def __exit_delete_mode(self):
        # Double click on user rebinded to user overview
        self.__label.config(text="All Users")
        self.__users_list.config(highlightthickness=0)
        self.__users_list.bind('<Double-1>', self.__get_user)
        self.__exit_button.pack_forget()  # Hide the exit button

    def __confirm_delete(self, event):
        # Ask if use wants to delete selected user
        selected_user = self.__users_list.curselection()
        if selected_user:
            selected_field = self.__users_list.get(selected_user[0])
            username = selected_field.split(":")[0].strip()
            if username == self.__controller.app_controller.get_current_user("username"):
                messagebox.showerror("Deletion Error","The current user selected is your current user!")
                self.__exit_delete_mode()
            else:

                if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {username}?"):
                    self.__delete_user(username)
                    self.__exit_delete_mode()

    def __delete_user(self, username):
        self.__controller.delete_user(username)  
        self.__users_list.delete(tk.ACTIVE)
        messagebox.showinfo("User Deleted", f"User {username} has been deleted.")

    def __get_user(self, event):
        # Get user that was selected
        selected_user = self.__users_list.curselection()
        if selected_user:
            selected_field = self.__users_list.get(selected_user[0])
            username = selected_field.split(":")[0].strip()
            user = self.__controller.get_user(username)
            self.__controller.app_controller.show_user_frame("User Details", user)





class ShowUserDetailsFrame(tk.Frame):
    # This class will require 1 additional arguments compared to others
    def __init__(self, parent, controller,user=None):
        super().__init__(parent)
        self.__controller = controller
        # get user details from controller
        if user is not None:
            self.__user = user[0][0]
    
        else:
            self.__user = self.__controller.app_controller.get_current_user()
        if self.__user == self.__controller.app_controller.get_current_user():
            self.__current_user = True
        else:
            self.__current_user = False
        # Frame Layout
        label = ttk.Label(self, text="User Details", font=("Arial", 20))
        label.pack(pady=10)
        self.__details_label = ttk.Label(self, text="", justify="left")
        self.__details_label.pack()
        details = f"Username: {self.__user['username']}\nDescription: {self.__user['description']}\nPermissions: {self.__user['permissions']}"
        self.__details_label.config(text=details)
        password_button = ttk.Button(self,text="Change Password",command=self.__password_window)
        password_button.pack(pady=10)

        # If user has admin permissions they can edit the user
        if self.__controller.app_controller.authenticate("X"):
            edit_button = ttk.Button(self,text="Edit User",command=self.__show_edit_form)
            edit_button.pack(pady=10)
        self.__edit_frame = None



    def __password_window(self):
        # Show password window
        app = password_change(self.__user["username"],self.__controller)
        app.mainloop()


    
    def __show_edit_form(self):
        # Allow user to edit user
        if self.__edit_frame is not None:
            self.__edit_frame.destroy()
        # Config
        self.__edit_frame = tk.Frame(self)
        self.__edit_frame.pack(pady=10)
        self.__form = Edit_form(self.__edit_frame,self.__user)
        self.__form.pack(pady=10)
        self.__form.save_button.config(command=self.__save_changes)
   
    def __save_changes(self):
        # Make sure user has chosen a privellege
        if self.__form.permissions_vars["Read (R)"].get() == False:
            messagebox.showerror("Editting Error","This user must have at least Read Permissions")
        elif self.__current_user == True and self.__form.permissions_vars["Execute (X)"].get() == False:
            messagebox.showerror("Editting Error", "The user can revoke privilleges from themselves. Get another administrator to")
        # Try sending new data to API
        else:
            # Update user details with values from the entry fields
            old_username = self.__user['username']
            selected_permissions = [val for key, val in self.__form.permissions_options.items() if self.__form.permissions_vars[key].get()]
            self.__user['username'] = self.__form.username_entry.get()
            self.__user['description'] = self.__form.description_entry.get()
            self.__user['permissions'] = selected_permissions
            
            if self.__user['username'] != old_username:
                valid = self.__controller.check_username(self.__user['username'])
                if not valid:
                    messagebox.showerror("Creation Error", "Username cannot be blank or already exist!")
                    self.__edit_frame.destroy()
                    self.__edit_frame = None
                    return
            self.__controller.update_user(old_username,self.__user)
            # Update the details label
            details = f"Username: {self.__user['username']}\nDescription: {self.__user['description']}\nPermissions: {self.__user['permissions']}"
            self.__details_label.config(text=details)

            self.__edit_frame.destroy()
            self.__edit_frame = None







class AddUserFrame(User_Form):
    def __init__(self, container, controller):
        super().__init__(container)
        self.__controller = controller
        self.__user = {
            "username": "",
            "password_hash": "",
            "description": "",
            "permissions": []  
        }
        # Reconfig of userform for adduserframe
        self.header = ttk.Label(self, text="Add User", font=("Arial", 20))
        self.password_label = ttk.Label(self, text="Enter Password").grid(row=4, column=0, pady=5)
        self.password_entry = ttk.Entry(self, show="*")
        self.confirmation_label = ttk.Label(self, text="Confirm Password").grid(row=5, column=0, pady=5)
        self.confirmation_password_entry = ttk.Entry(self, show="*")
        self.header.grid(row=0, column=1, columnspan=2)
        self.password_entry.grid(row=4, column=1, pady=5)
        self.confirmation_password_entry.grid(row=5, column=1, pady=5)
        
        self.save_button.grid(row=10, column=0, columnspan=2, pady=10)
        self.save_button.config(command=self.submit)
    
    def submit(self):
        # Change submit logic from userform
        if self.permissions_vars["Read (R)"] == False:
            messagebox.showerror("Creation Error","User Must have at least Read permissions")
        else:
            password = self.password_entry.get()
            confirmation_password = self.confirmation_password_entry.get()
            # Ensure passwords match up
            if password == confirmation_password:
                username = self.username_entry.get()
                description = self.description_entry.get()
                
                # Get selected permissions as a list
                selected_permissions = [val for key, val in self.permissions_options.items() if self.permissions_vars[key].get()]
                # Ensure user has selected permissions
                if not selected_permissions:
                    messagebox.showerror("Permission Error", "At least Read permission is required!")
                    return
                # See if user has passed both username and passsword requirements
                username_pass = self.__controller.check_username(username)
                password_pass, message = self.__controller.check_password(password)
                # Add the new user if valid
                if username_pass and password_pass:
                    self.__user['username'] = username
                    self.__user['description'] = description
                    self.__user['permissions'] = selected_permissions
                    self.__user['password_hash'] = self.__controller.convert_password(password)
                    self.__controller.add_user(self.__user)
                    self.__controller.app_controller.show_user_frame("Show Users")
                else:
                    if not username_pass:
                        messagebox.showerror("Creation Error", "Username cannot be blank or already exist!")
                    else:
                        messagebox.showerror("Password Denied", message)
            else:
                messagebox.showerror("Password Error", "Passwords do not Match Up")

#------------------------Window Widgets------------------------------#

class login_page(EntryWindow):
    def __init__(self,controller):
        EntryWindow.__init__(self)
        # COnfig for login page
        self.__controller = controller
        self.title("Login Window")
        self.label1.config(text="Usenrame")
        self.label2.config(text="Password")
        self.submit_button.config(command=self.submit_login)
        self.bind('<Return>', self.submit_login)

    def submit_login(self,event=None):
        # Send credentials to API
        username = self.entry1.get()
        password = self.entry2.get()
        success = self.__controller.login(username, password)
        if success:
            self.destroy()
            
        else:
            messagebox.showerror("Login Error", "Username or password is incorrect")

    
class password_change(EntryWindow):
    def __init__(self,username,controller):
        EntryWindow.__init__(self)
        # Attempt to change password
        self.__username = username
        self.__controller = controller
        # Reconfig of Entrywindow
        self.title("Password Change Window")
        self.label1.config(text="Enter New Password")
        self.label2.config(text="Confirm New Password")
        self.submit_button.config(command=self.submit)
        self.bind('<Return>', self.submit)
        self.entry1.config(show="*")

    def submit(self,event=None):
            # Make sure passwords match up
            password = self.entry1.get()
            password_confirmation = self.entry2.get()
            if password == password_confirmation:
                result,message = self.__controller.check_password(password)
                if result == True:
                    # Hash new password and send to api to update for user
                    password_hash = self.__controller.convert_password(password)
                    success = self.__controller.change_password(self.__username,password_hash)
                    if not success:
                        messagebox.showerror("Unable to Change","Password was unable to change, please try again later")
                    else:
                        messagebox.showinfo("Success","Password Changed Succesfully!")
                    self.destroy()
                        
                else:
                    messagebox.showerror("Password Denied",message) 
            else:
                messagebox.showerror("Change Error","Password's do not match")

        


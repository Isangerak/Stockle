import tkinter as tk
from tkinter import ttk 
from tkinter import messagebox

# -------------------------- GLOBAL VARIABLES -------------------------

selectionbar_color = '#eff5f6'
sidebar_color = '#FFD369'
header_color = '#393E46'
visualisation_frame_color = "#EEEEEE"

# ------------------------------- ROOT WINDOW  ----------------------------------


class TkinterApp(tk.Tk):

    def __init__(self,user_controller,stock_controller,app_controller):
        tk.Tk.__init__(self)
        self.app_controller = app_controller
        self.user_controller = user_controller
        self.stock_controller = stock_controller
        self.__current_frame = None   
        self.unsaved_changes = False

        
        # ------------- LOADING OVERLAY FOR API DOWNTIME ---------
        self.__overlay = None

        # ------------- BASIC APP LAYOUT -----------------
        self.geometry("1100x700")
        self.title('Stock Management System')
        self.config(background=selectionbar_color)
        icon = tk.PhotoImage(file='Stockle.png')
        self.iconphoto(True, icon)

        # ---------------- HEADER ------------------------
        self.__header = tk.Frame(self, bg=header_color)


        # Alerts Button
        alert_button = ttk.Button(self.__header,command=self.__show_alerts,text="Stock Alerts")
        alert_button.place(relx=0,rely=0.2,relwidth=0.08,relheight=0.6)


        # Sync Button
        self.__sync_image = tk.PhotoImage(file="sync.png")
        sync_button= ttk.Button(self.__header, image=self.__sync_image,command= self.__send_sync_request)
        sync_button.place(relx=0.85,rely=0.2,relwidth=0.06,relheight=0.6)

        # Account Button
        self.__account_button = tk.Button(self.__header, text="User", relief="raised")
        self.__account_button.place(relx=0.92,rely=0.2,relwidth=0.06,relheight=0.6)
        self.__header.place(relx=0.1, rely=0, relwidth=0.9, relheight=0.1)
            # Create the submenu for Button
        self.__submenu = SubMenu(self)

        # Bind the button to show the submenu on click
        self.__account_button.bind("<Button-1>", self.__submenu.show_submenu)
        
        
        

        # ---------------- SIDEBAR -----------------------
            # CREATING FRAME FOR SIDEBAR
        self.__sidebar = tk.Frame(self, bg=sidebar_color)
        self.__sidebar.place(relx=0, rely=0, relwidth=0.1, relheight=1)

            #Logo
        self.__brand_frame = tk.Frame(self.__sidebar, bg=sidebar_color)
        self.__brand_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.__stock_logo = icon.subsample(9)
        logo = tk.Label(self.__brand_frame, image=self.__stock_logo, bg=sidebar_color)
        logo.place(x=5, y=20)
            # SUBMENUS IN SIDE BAR
        self.__submenu_frame = tk.Frame(self.__sidebar, bg=sidebar_color)
        self.__submenu_frame.place(relx=0, rely=0.2, relwidth=1, relheight=1)
        menu_options=  ["Dashboard",
                        "Product Search"
                        ]

        # Check User is Authorised and show frames based on permission
        if self.app_controller.authenticate("W"):
            menu_options.append("Edit Stock")

        menu_options.append("Rule Groups")
        menu_options.append("Orders")
       
        if self.app_controller.authenticate("X"):
            menu_options.append("Users")
        

       
        submenu1 = SidebarSubMenu(self.__submenu_frame, sub_menu_heading='SUBMENU',sub_menu_options=menu_options)

        # Assign Commands to run for each option
        submenu1.options["Product Search"].config(
            command=lambda: self.stock_show_frame("Product Search"))
        
        submenu1.options["Dashboard"].config(
            command=lambda: self.stock_show_frame("Dashboard"))
        try:
            submenu1.options['Edit Stock'].config(
            command=lambda: self.stock_show_frame("Add From List")
        )
            submenu1.options["Users"].config(
                command=lambda: self.user_show_frame("Show Users")
        )
           
        except:
            pass

     
    
        submenu1.options["Rule Groups"].config(
            command=lambda:self.stock_show_frame("Rule Groups"))

        submenu1.options["Orders"].config(
            command=lambda:self.stock_show_frame("Orders"))


        submenu1.place(relx=0, rely=0.025, relwidth=1, relheight=1)
        # -------------------- COTAINER SETTINGS ----------------------------

        self.__container = tk.Frame(self)
        self.__container.config(highlightbackground="#808080", highlightthickness=0.5)
        self.__container.place(relx=0.1, rely=0.1, relwidth=0.9, relheight=0.9)

        

    # ------------ LOCKING & UNLOCKING MECHANICS FOR API DOWNTIME ----------------
    def show_overlay(self):
        if self.__overlay is None:
            self.__overlay = LoadingOverlay()
            self.__overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
           
            # Force immediate UI update
            self.update_idletasks()
                

    def remove_overlay(self):
        if self.__overlay is not None:
            self.__overlay.destroy()
            self.__overlay = None

    def show_fatal_error(self):
        # Remove overlay first
        messagebox.showerror("Critical Error", "API Unavailable, please try again later")
        self.on_closing()
    # -------------------- OTHER FUNCTIONS ----------------------------

    def user_show_frame(self, frame_name,*args):
        # Dont let user leave if there are unsaved changes
        if not self.unsaved_changes:
            if self.__current_frame is not None:
                
                self.__current_frame.pack_forget()
            # Pass arguments to frame class if they ned it
            if args:
                arguments = [arg for arg in args]
                self.__current_frame = self.user_controller.get_frame(frame_name,self.__container,arguments)
                self.__current_frame.pack(fill="both", expand=True)
            else:
                self.__current_frame = self.user_controller.get_frame(frame_name, self.__container)
                self.__current_frame.pack(fill="both", expand=True)
        else:
            messagebox.showerror("UNSAVED CHANGES!","Please save or discard Changes!")

  
    def stock_show_frame(self, frame_name,*args):
        # Do not let user leave if there are unsaved changes
        if not self.unsaved_changes:
                
            if self.__current_frame is not None:
            
                self.__current_frame.pack_forget()
            # Pass arguments to frame class if they need it
            if args:
                arguments = [arg for arg in args]
                self.__current_frame = self.stock_controller.get_frame(frame_name,self.__container,arguments)
                self.__current_frame.pack(fill="both", expand=True)
            else:
                self.__current_frame = self.stock_controller.get_frame(frame_name, self.__container)
                self.__current_frame.pack(fill="both", expand=True)
        else:
            messagebox.showerror("UNSAVED CHANGES!","Please save or discard Changes!")


   

    def on_closing(self):
        self.app_controller.app_shutdown = True
        # Cleanup overlay if it was showing
        if self.__overlay:
            self.__overlay.destroy()
        
        #  destroy other components
        self.app_controller.clear_current_user()
        self.destroy()
        self.quit()


    def logout(self):
        self.app_controller.clear_current_user()
        self.destroy()
        self.quit()
    
    def __send_sync_request(self):
        response,status_code = self.stock_controller.sync_request("Requesting Sync")
        if status_code == 200:
            return True
        else:
            return False
    
    
      

    def __show_alerts(self):
        StockAlertWindow(self)

# ----------------------------- OTHER WIDGETS ---------------------------------

class SidebarSubMenu(tk.Frame):
    # Sidebar for the main window
    def __init__(self, parent, sub_menu_heading, sub_menu_options):
        
        tk.Frame.__init__(self, parent)
        self.config(bg=sidebar_color)
        self.__sub_menu_heading_label = tk.Label(self,
                                               text=sub_menu_heading,
                                               bg=sidebar_color,
                                               fg="#333333",
                                               font=("Arial", 10)
                                               )
        self.__sub_menu_heading_label.place(x=30, y=10, anchor="w")

        sub_menu_sep = ttk.Separator(self, orient='horizontal')
        sub_menu_sep.place(x=30, y=30, relwidth=0.8, anchor="w")
        # Set options variable for the frame buttons
        self.options = {}
        for n, x in enumerate(sub_menu_options):
            self.options[x] = tk.Button(self,
                                        text=x,
                                        bg=sidebar_color,
                                        font=("Arial", 9, "bold"),
                                        bd=0,
                                        cursor='hand2',
                                        activebackground='#ffffff',
                                        )
            self.options[x].place(x=30, y=45 * (n + 1), anchor="w")



class SubMenu:
    def __init__(self, parent):
        # Top header for the main view
        self.__parent = parent

        # Create the submenu
        self.__menu = tk.Menu(parent, tearoff=0)

        # Add the 'Close' option
        self.__menu.add_command(label="X", command=self.__close_submenu)

        # Add other options to the submenu
        self.__menu.add_command(label="User Details",command=lambda: self.__parent.user_show_frame("User Details"))
        self.__menu.add_command(label="Sign Out", command=self.__logout)

    def show_submenu(self, event):
        # Position the submenu just below the main button
        self.__menu.post(event.x_root, event.y_root)
        # Bind the root to detect clicks outside the submenu
        self.__parent.bind("<Button-1>", self.hide_submenu)

    def __logout(self):
        #  run logout function
        self.__parent.logout()
        

    def hide_submenu(self, event):
        # Unpost the submenu
        self.__menu.unpost()
        # Unbind the click event on the root
        self.__parent.unbind("<Button-1>")


    def __close_submenu(self):
        self.hide_submenu(None)





class StockAlertWindow:
    def __init__(self,parent):
        self.__parent = parent
        message_window = tk.Toplevel(self.__parent)
        message_window.title("Stock Messages")
        message_window.geometry("400x300")
        #Clear Button
        x_button = tk.Button(message_window,text="X",command=self.__clear_window,bg="RED")
        x_button.pack(anchor="ne")
        #Frame to Hold messages
        self.__message_frame = ttk.Frame(message_window)
        self.__message_frame.pack(fill=tk.BOTH,expand=True,padx=10,pady=10)

        messages = self.__get_messages()
        # Format and show all stock Alert messages
        if messages:
            for name,message in messages:
                if name != None:
                    msg_label = ttk.Label(self.__message_frame,text=f"Product {name} has {message}",font=("Arial",12))
                    msg_label.pack(anchor="w",pady=2)
              
        else:
            label = ttk.Label(self.__message_frame,text="Nothing to see here",font=("Arial",14))
            label.pack()

    def __get_messages(self):
        alerts = self.__parent.stock_controller.return_stock_alerts()
        return alerts

    def __clear_messages(self):
        self.__parent.stock_controller.clear_stock_alerts()


    def __clear_window(self):
        self.__clear_messages()
        for widget in self.__message_frame.winfo_children():
            widget.destroy()
        # Show empty frame window
        label = ttk.Label(self.__message_frame, text="Nothing to see here", font=("Arial", 14))
        label.pack()

    


class LoadingOverlay(tk.Frame):
    def __init__(self):
        super().__init__()
        self.configure(bg='#333333', bd=0, highlightthickness=0)
        
        # Cover entire client area of main window
        
        # Loading message
        self.__loading_label = tk.Label(self, 
                                    text="Reconnecting to API...", 
                                    fg='white', 
                                    bg='#333333',
                                    font=('Arial', 14))
        self.__loading_label.place(relx=0.5, rely=0.4, anchor='center')
        
        # Progress bar
        self.__progress = ttk.Progressbar(self, 
                                      mode='indeterminate',
                                      length=200)
        self.__progress.place(relx=0.5, rely=0.5, anchor='center')
        self.__progress.start()

    def destroy(self):
        # Stop the autoincrement callbacks
        self.__progress.stop()
        # destroy the progress bar and the overlay
        if self.__progress:
            self.__progress.destroy()
        super().destroy()
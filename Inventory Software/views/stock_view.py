import tkinter as tk
from tkinter import ttk , filedialog
from tkinter import messagebox
from views.user_view import EntryWindow
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# How to make a product search page and work with table: https://www.youtube.com/watch?v=i4qLI9lmkqw


#----------------------WINDOWS-----------------------#
class ChangeQuantity(EntryWindow): # Frame to allow user to enter new quantity for the product selected
    def __init__(self,parent,product_values,selected_record):
        super().__init__()
        # Parent is the SearchStock Frame
        # Product values contents example: ('1', 'Laptop', 'Electronics', 'Electronics', '50')
        self.__parent = parent
        self.__product_values = product_values
        self.__selected_record = selected_record
        # Alter EntryWindow base properties for changequantity
        self.title(f"Edit Quantity for Product ID {self.__product_values[0]}")
        self.label1.config(text="Enter new Quantity")
        self.label2.grid_forget()
        self.entry2.grid_forget()
        self.submit_button.config(command=self.__submit)
        self.bind('<Return>',self.__submit)

    def __submit(self, event=None):
        value = self.entry1.get()
        # Ensure that input was a number
        try:
            quantity = int(value)
            if quantity >= 0:
                # Number was valid set new values to quantity set
                self.__parent.new_values[self.__product_values[0]] = quantity

                # Make sure that true original value is not overwritten if quantity changed twice
                if self.__product_values[0] not in self.__parent.original_values.keys():
                    self.__parent.original_values[self.__product_values[0]] = self.__product_values[4]

                # Update the Treeview item, quantity for treeview has to be string
                self.__parent.tableview.item(self.__selected_record,text="",values=(self.__product_values[0],self.__product_values[1],self.__product_values[2],self.__product_values[3],str(quantity)))
                # Trigger Unsaved Changes Flag
                if not self.__parent.controller.app_controller.get_unsaved_changes:
                    self.__parent.controller.app_controller.set_unsaved_changes(True)
                self.destroy()
            else:
                messagebox.showerror("Quantity Error", "Number cannot be negative!")
        except ValueError:
            messagebox.showerror("Input Error", "Input must be a whole positive integer!")

        

#----------------------FRAMES-----------------------#
# --------------------------------------------------------------- PRODUCT FRAMES
class SearchStock(tk.Frame): # General frame that shows products in a tableview with a operational search bar
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.highlighted_items = []
        #Frames
        search_frame = ttk.LabelFrame(self,text="Search",height=100)
        search_frame.pack_propagate(False) # Prevent lael frame from resizing
        stock_frame = ttk.LabelFrame(self,text="Results")
        search_frame.pack(side=tk.TOP,fill="x",expand=False,padx=10,pady=5)
        stock_frame.pack(side=tk.BOTTOM,fill="both",expand=True,padx=10,pady=5)

        # Table
        self.tableview = ttk.Treeview(stock_frame,columns=(1,2,3,4,5),show="headings",height="6")
        self.tableview.pack(side=tk.LEFT, fill="both", expand=True)
        self.tableview.heading(1,text="Product ID")
        self.tableview.heading(2,text="Product Name")
        self.tableview.heading(3,text="Category")
        self.tableview.heading(4,text="Rule Group")
        self.tableview.heading(5,text="Quantity")
         
        # Search Bar & Button
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame,textvariable=self.search_var)
        self.search_entry.place(relx=0.125,rely=0.5,relwidth=0.75,anchor="w")
        search_button = ttk.Button(search_frame,text="Search",command=self.search)
        search_button.place(relx=0.875,rely=0.5,anchor="w")

        # Initial Values
        results,status_code = self.controller.get_stock_search("")
        self.update_results(results)
        self.tableview.bind("<Double-1>", self.get_product)



    def search(self):
        # Get search term and retrieve search result 
        search_term = self.search_var.get()
        # Dont require status code
        results, _ = self.controller.get_stock_search(search_term)
        self.update_results(results)



    def update_results(self,results):
        # delete everything in tableview
        self.tableview.delete(*self.tableview.get_children())
        # Input new results
        for result in results:
            self.tableview.insert('', 'end', values=result)

    def get_product(self,event):
        # Get selected item
        selected_product = self.tableview.selection()
        if selected_product:
            # Show product overview page wih acquired prod id
            product = self.tableview.item(selected_product)
            product_id = product['values'][0]
            self.controller.app_controller.show_stock_frame("Product Overview",product_id)


class ProductOverview(tk.Frame):
    def __init__(self,parent,controller,product_id):
        # Show product overview page for given prod id
        super().__init__(parent)
        self.__controller = controller
        product_info = self.__controller.get_product_info(product_id)
        # Frame Layout
        label = ttk.Label(self, text=f"Product Info on {product_info["Name"]}", font=("Arial", 20))
        label.pack(pady=10)
        self.__details_label = ttk.Label(self, text="", justify="left")
        self.__details_label.pack()
        # Format details into viewable string
        details = f" Product ID: {product_info["ID"]} \n Product Name: {product_info["Name"]} \n Product Category: {product_info["Category"]} \n Selling Price: £{product_info["Selling Price"]}  \n  VAT: {product_info["VAT"]}% \n Currently In Stock: {product_info["Quantity"]} \n  Current Rule In Place: {product_info["Rule"]}"
        self.__details_label.config(text=details)




        
class AddFromList(SearchStock):
    def __init__(self,parent,controller):
        super().__init__(parent,controller)
        # Lets user add quantity for products from the product list
        # Dictionary of Product_id and changed quantity to retain information when handling multiple changes
        self.new_values = {}   
        # Hold original values in case nothing is changed - prevents a redundant call to the API
        self.original_values = {}
        
        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.TOP, fill="x", expand=False, padx=10, pady=5)
        cancel_button = ttk.Button(self,text="Cancel Changes",command=self.__cancel_changes)
        save_button = ttk.Button(self,text="Save Changes",command=self.__save_changes)
        cancel_button.pack(side=tk.RIGHT, padx=(0, 10))
        save_button.pack(side=tk.RIGHT,padx=(0,10))
        self.tableview.bind("<Double-1>", self.__edit_quantity)


    def __edit_quantity(self,event=None):
        # Grab Record Numer
        selected_record = self.tableview.focus()
        if selected_record:
            self.controller.app_controller.set_unsaved_changes(True)
            # Grab Record Values
            product_values = self.tableview.item(selected_record,'values') 
            # Display the Entry Window for the new quantity
            window = ChangeQuantity(self,product_values,selected_record)
            window.mainloop()
           
        
    def __save_changes(self):
        # Send new values to be formatted to send to API
        success = self.controller.update_stock_count(self.new_values)
        if success:
            self.controller.app_controller.set_unsaved_changes(False)
            messagebox.showinfo("Updated Stock","Stock Updated Successfully!")
        else:
            messagebox.showerror("API is currently unavailable","unable to connect, try again later")

    
    def __cancel_changes(self):
        self.controller.app_controller.set_unsaved_changes(False)
        self.search()
        messagebox.showinfo("Reverted Changes","Original Stock now showing")



    




class ProductMultipleChoice(SearchStock): # Allows for multiple products to be selected, used in adding / editing rulegroups
    def __init__(self,parent,controller):
        super().__init__(parent,controller)
        self.tableview.configure(selectmode='extended')
        #  Create Reset button
        button_frame = ttk.Frame(self)
        button_frame.pack(side=tk.TOP, fill="x", expand=False, padx=10, pady=5)
        reset_button = ttk.Button(button_frame,text="Reset",command=self.__reset_selected)
        reset_button.pack()


        # Configure Tags
        self.tableview.tag_configure('default', background='white')  # Reset background color
        self.tableview.tag_configure('highlighted', background='lightblue')  # Change background color


    def get_product(self,event):
        # Get the item (row) that was clicked on
        selected_item = self.tableview.identify_row(event.y)
        
        if selected_item:
            # Get the current tags of the item to check if it's highlighted
            tags = self.tableview.item(selected_item, 'tags')
            if 'highlighted' in tags:
                # If already highlighted, unhighlight and remove from selection
                self.tableview.item(selected_item, tags=())  # Remove the highlight tag
                self.highlighted_items.remove((self.tableview.item(selected_item)['values'][0],self.tableview.item(selected_item)['values'][1])) # Remove from selection list
                
            else:
                # If not highlighted, highlight and add to selection
                self.tableview.item(selected_item, tags=('highlighted',))  # Add the highlight tag
                self.highlighted_items.append((self.tableview.item(selected_item)['values'][0],self.tableview.item(selected_item)['values'][1]))  # Add ID to selection list

    def update_results(self,results):
        # Delete everything in tableview and highlight the items 
        self.tableview.delete(*self.tableview.get_children())
        highlighted_ids = []
        for item in self.highlighted_items:
            # item[0] is id of product
            highlighted_ids.append(item[0])
        # Update data with new values for table
        for result in results:
            self.tableview.insert('', 'end', values=result)
        # Iterate through tableview and highlight if it was before new search
        for item in self.tableview.get_children():
            if self.tableview.item(item)['values'][0] in highlighted_ids:
                self.tableview.item(item, tags=('highlighted',))

    def __reset_selected(self):
        # Set all highlighted data back to original colour 
        self.highlighted_items = []
        for item in self.tableview.get_children():
            self.tableview.item(item,tags=())
    

    def highlight_items(self, product_ids):
        # Highlight all rows that match the given product IDs
        self.highlighted_items = []  # Clear previous selections
        # Iterate and highlight data that has the product id in list
        for item in self.tableview.get_children():
            row_values = self.tableview.item(item)["values"]
            if row_values and row_values[0] in product_ids:  # Check if product_id matches
                self.tableview.item(item, tags=('highlighted',))  # Apply highlight tag
                self.highlighted_items.append((row_values[0], row_values[1]))  # Add to selection
            else:
                self.tableview.item(item, tags=())  # Remove highlight if not in list



# ---------------------------------------------------------- RULE ORIENTED FRAMES 
class RuleGroupForm(tk.Frame):
    def __init__(self, parent, controller, title="Rule Group Form"):
        super().__init__(parent)
        self.controller = controller
        self.selected_choice = tk.StringVar(self)

        # Title Label
        self.title_label = ttk.Label(self, text=title, font=("Arial", 14, "bold"))
        self.title_label.pack(pady=10)

        # RuleGroup Name
        self.name_label = ttk.Label(self, text="Enter RuleGroup Name")
        self.name_label.pack(pady=10)
        self.name_entry = ttk.Entry(self)
        self.name_entry.pack(pady=10)

        # Minimum Stock
        self.min_label = ttk.Label(self, text="Enter Stock amount to trigger at")
        self.min_label.pack(pady=10)
        self.min_entry = ttk.Entry(self)
        self.min_entry.pack(pady=10)

        # Category Selection
        self.category_label = ttk.Label(self, text="Choose Category to govern")
        self.category_label.pack()
        self.categories = self.controller.get_categories()
        self.categories.append('None')
        self.category_menu = ttk.OptionMenu(self, self.selected_choice, self.categories[0], *self.categories)
        self.category_menu.pack()
        self.selected_choice.trace("w", self.on_option_change)

        # Product Selection Table
        self.table_frame = ttk.Frame(self)
        self.tableview = ProductMultipleChoice(self.table_frame, self.controller)
        self.tableview.pack()

        # Submit Button
        self.submit_button = tk.Button(self, text="Submit", command=self.submit_action)
        self.submit_button.pack(pady=10)

    def on_option_change(self, *args):
        selected = self.selected_choice.get()
        if selected == "None":
            self.table_frame.pack()
        else:
            self.table_frame.pack_forget()

    def submit_action(self):
        raise NotImplementedError("Subclasses must implement submit_action()")




class RuleGroups(SearchStock): # Shows general frame for all of rulegroups
    def __init__(self,parent,controller):
        super().__init__(parent,controller)
        self.__delete_mode = False # Flag to indicate delete mode
        # Reconfigeration of display from SearchStock
        # Only can delete if have Write permissions
        can_delete = self.controller.app_controller.authenticate("W")
        self.__button_frame = ttk.Frame(self)
        self.__button_frame.pack(side=tk.TOP, fill="x", expand=False, padx=10, pady=5)
        if can_delete:
            add_button = ttk.Button(self.__button_frame,text="Add Rulegroup",command=lambda:self.controller.app_controller.show_stock_frame("Add Rule Group"))
            delete_button = ttk.Button(self.__button_frame,text="Delete rulegroup",command=self.__enter_delete_mode)
            add_button.pack(side=tk.RIGHT,padx=(0,10))
            delete_button.pack(side=tk.RIGHT,padx=(0,10))

            self.__exit_button = ttk.Button(self.__button_frame, text="Exit Delete Mode", command=self.__exit_delete_mode)
            self.__exit_button.pack(side="right", padx=(0, 5))
            self.__exit_button.pack_forget()  # Hide initially

        
        # Configure Tableview for new instance
        new_columns = ("1", "2", "3", "4")
        new_headings = ["Rule ID", "Rule Name", "Category Applied To", "Minimum Stock Trigger"]

        #   Update with new set
        self.tableview["columns"] = new_columns

        #   Update the headings
        for col, heading in zip(new_columns, new_headings):
            self.tableview.heading(col, text=heading)


        # Initial Values
        results = self.controller.get_rule_search("")
        self.update_results(results)
        self.tableview.bind("<Double-1>", self.__get_rule)


    def search(self):
        search_term = self.search_var.get()
        results = self.controller.get_rule_search(search_term)
        self.update_results(results)



    def __get_rule(self,event):
        # Get selected item
        selected_rule = self.tableview.selection()
        if selected_rule:
            rule = self.tableview.item(selected_rule)
            rule_id = rule['values'][0]
            self.controller.app_controller.show_stock_frame("RuleGroup Overview",rule_id)


    def __enter_delete_mode(self):
        self.__delete_mode= True
        self.tableview.bind('<Double-1>',self.__confirm_delete)
        self.__exit_button.pack(side='right',padx = (0,5))

    
    def __exit_delete_mode(self):
        self.__delete_mode = False
        self.tableview.bind('<Double-1>',self.__get_rule)
        self.__exit_button.pack_forget()

    
    def __confirm_delete(self,event):
        selected_rule = self.tableview.selection()
        if selected_rule:
            selected_field = self.tableview.item(selected_rule)
            rule_id = selected_field['values'][0]
            if messagebox.askyesno("Confirm Delete",f"Are you sure you want to delete rule: {rule_id}, {selected_field['values'][1]}"):
                self.controller.delete_rulegroup(rule_id)
                messagebox.showinfo("RuleGroup Deleted",f"Rule with ID {rule_id} deleted")
                self.search()



class RuleOverview(tk.Frame):
    def __init__(self,parent,controller,rule_id):
        super().__init__(parent)
        self.__controller = controller
        # Get rule information for rule_id given
        self.__rule_info = self.__controller.get_rule_info(rule_id[0][0])
        # Frame Layout
        label = ttk.Label(self, text=f"RuleGroup Info on {self.__rule_info["Name"]}", font=("Arial", 20))
        label.pack(pady=10)
        self.__details_label = ttk.Label(self, text="", justify="left")
        self.__details_label.pack()
        # Configure details in a readdable format
        details = f" Rule ID: {self.__rule_info["ID"]} \n  Stock Level Triggered At: {self.__rule_info["Minimum Stock"]}"
        if not self.__rule_info["Category"] == "None":
            details += f"\n Category Applied To: {self.__rule_info["Category"]}"
        else:
            # Show a tableview for the products it is governing if category is None
            self.__product_table = ttk.Treeview(self, columns=("Product Id", "Name","Category", "Stock"), show="headings")
            self.__product_table.heading("Product Id", text="Product ID")
            self.__product_table.heading("Name", text="Name")
            self.__product_table.heading("Category", text="Category")
            self.__product_table.heading("Stock", text="Stock")
            for product in self.__rule_info["Products"]:
                self.__product_table.insert("", "end", values=product)
            self.__product_table.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.__details_label.config(text=details)
        if self.__controller.app_controller.authenticate("W"):
            edit_button = ttk.Button(self,text="Edit RuleGroup",command=self.__edit)
            edit_button.pack(pady=10)
        
    def __edit(self):
        # Send user to the edit rule frame with curent rule info
        if self.__rule_info["Category"] == "None":
            product_ids = []
            for product in self.__rule_info["Products"]:
                product_ids.append(product[0])
            self.__rule_info["Products"] = product_ids
        self.__controller.app_controller.show_stock_frame("Edit Rule Group",self.__rule_info)



class EditRuleGroup(RuleGroupForm): # Show edit form for rule
    def __init__(self, parent, controller, rulegroup_data):
        super().__init__(parent, controller, title="Edit Rule Group")
        self.populate_fields(rulegroup_data[0][0])
        self.__new_rule = {}
        self.__new_rule["Old Name"] = rulegroup_data[0][0]["Name"]
        self.__new_rule["Old Category"] = rulegroup_data[0][0]["Category"]
        self.__new_rule["ID"] = rulegroup_data[0][0]["ID"]
    def populate_fields(self, rulegroup_data):
        self.name_entry.insert(0, rulegroup_data['Name'])
        self.min_entry.insert(0, rulegroup_data['Minimum Stock'])
        self.selected_choice.set(rulegroup_data['Category'])
        
        if rulegroup_data['Category'] == "None":
              # If not highlighted, highlight and add to selection
                self.tableview.highlight_items(rulegroup_data["Products"])

    def submit_action(self):
        # Get data from the forms
        category = self.selected_choice.get()
        rule_name = self.name_entry.get()
        min_stock = self.min_entry.get()
        # Add to dictionary
        self.__new_rule["Category"] = category
        self.__new_rule["Name"] = rule_name
        self.__new_rule["Minimum Stock"] = min_stock
        if category == 'None':
            # Get product ids if independent rule group
            product_ids = [item[0] for item in self.tableview.highlighted_items]
            if  isinstance(product_ids,str):
                ids = [int(x) for x in product_ids.strip("()").split(",")]
            else:
                ids = product_ids
            self.__new_rule["Product IDs"] = ids
            valid, message = self.controller.update_rulegroup(self.__new_rule)
        else:
            valid, message = self.controller.update_rulegroup(self.__new_rule)

        if not valid:
            messagebox.showerror("Update Error", message)
        else:
            messagebox.showinfo("Rule Updated", "Rule has been updated successfully!")
            self.controller.app_controller.show_stock_frame("Rule Groups")




class AddRuleGroup(RuleGroupForm):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, title="Add Rule Group")

    def submit_action(self):
        # Get data from the forms
        category = self.selected_choice.get()
        rule_name = self.name_entry.get()
        min_stock = self.min_entry.get()
        
        if category == 'None':
            # Get product ids from the tableview if independent rule group
            product_ids = [item[0] for item in self.tableview.highlighted_items]
            if product_ids:
                if len(product_ids) > 1:
                    product_ids = tuple(product_ids)
                else:
                    product_ids = (product_ids[0],)
            else:
                product_ids = ()
            
            valid, message = self.controller.create_rulegroup(category, rule_name, min_stock, product_ids)
        else:
            valid, message = self.controller.create_rulegroup(category, rule_name, min_stock)

        if not valid:
            messagebox.showerror("Creation Error", message)
        else:
            messagebox.showinfo("Rule Created", "Rule has been added successfully!")
            self.controller.app_controller.show_stock_frame("Rule Groups")







# -------------------------------------------------------------------- ORDER FRAMES
class Orders(tk.Frame):
    def __init__(self,parent,controller):
        super().__init__(parent)
        self.__controller = controller

        # Frames
        self.__options_frame = ttk.LabelFrame(self,text="Options",height=100)
        self.__options_frame.pack_propagate(False) # Prevent lael frame from resizing
        self.__order_frame = ttk.LabelFrame(self,text="Products to Order")
        self.__options_frame.pack(side=tk.TOP,fill="x",expand=False,padx=10,pady=5)
        self.__order_frame.pack(side=tk.BOTTOM,fill="both",expand=True,padx=10,pady=5)

        # Display Options 
        send_to_txt = ttk.Button(self.__options_frame,text="Copy to a text file",command=self.__export_to_txt)
        send_to_txt.pack(side="left")

        self.__tableview = Order_table(self.__order_frame,self.__controller)
        self.__tableview.pack()


    
    def __export_to_txt(self):
        # Ask user where to save the file
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        
        # If user cancels, do nothing
        if not file_path:
            return

        # Get table data
        order_data = self.__tableview.get_order_list()

        # Write data to the selected file
        with open(file_path, "w") as file:
            file.write("Product ID\tProduct Name\tCurrent Stock\n")
            file.write("-" * 50 + "\n")
            for row in order_data:
                file.write("\t".join(map(str, row)) + "\n")



class Order_table(SearchStock):
    def __init__(self,parent,controller):
        super().__init__(parent,controller)

        # Configure Tableview for new instance
        new_columns = ("1", "2", "3")
        new_headings = ["Product_id", "Product Name", "Current Stock"]
        
        #   Update with new set
        self.tableview["columns"] = new_columns

        #   Update the headings
        for col, heading in zip(new_columns, new_headings):
            self.tableview.heading(col, text=heading)


        # Initial Values
        results = self.controller.get_order_list("")
        self.update_results(results)
        
    def search(self):
        search_term = self.search_var.get()
        results = self.controller.get_order_list(search_term)
        self.update_results(results)



    def get_order_list(self):
        # Extract data from the table
        items = self.tableview.get_children()
        return [self.tableview.item(item, "values") for item in items]


# ----------------------------------------------------------- DASHBOARD FRAMES
class DashboardFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.__controller = controller
        self.__dashboard_data = self.__controller.get_dashboard_data()
        # Top Section Layout
        top_frame = tk.Frame(self)
        top_frame.pack(fill="x", pady=10)

        # Donut Chart (Top Left)
        donut_frame = tk.Frame(top_frame)
        donut_frame.pack(side="left", padx=20)
        self.__create_donut_chart(donut_frame)

        # Top 10 Worst-Selling Products List (Top Middle)
        worst_selling_frame = tk.Frame(top_frame)
        worst_selling_frame.pack(side="left", padx=20)
        self.__create_worst_selling_list(worst_selling_frame)

        # Day's Revenue Display (Top Right)
        revenue_frame = tk.Frame(self)
        revenue_frame.pack(fill="both",expand=True, pady=10)
        self.__create_revenue_display(revenue_frame)

    def __create_donut_chart(self, frame):
        categories = []
        sales = []

        for item in self.__dashboard_data['Category Sales']:
            categories.append(item[0])
            sales.append(item[1])

        fig, ax = plt.subplots()
        ax.pie(sales, labels=categories, wedgeprops={'width': 0.4})
        ax.set_aspect("equal")
        
        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def __create_worst_selling_list(self, frame):
        label = ttk.Label(frame, text="Top 10 Worst Selling Products", font=("Arial", 16))
        label.pack(pady=10)

        # Listbox for displaying worst-selling products
        tableview = ttk.Treeview(frame,columns=(1,2,3,4,5),show="headings",height="6")
        tableview.pack(side=tk.LEFT, fill="both", expand=True)
        tableview.heading(1,text="Product ID")
        tableview.heading(2,text="Product Name")
        tableview.heading(3,text="Category")
        tableview.heading(4,text="Selling Price")
        tableview.heading(5,text="Total Sales")
        for product in self.__dashboard_data["Worst Products"]:
            tableview.insert('', 'end', values=product)



        
    def __create_revenue_display(self, frame):
        # Placeholder for revenue data (replace with actual data retrieval)
        label = ttk.Label(frame, text="Today's Revenue", font=("Arial", 16))
        label.pack(pady=10)

        revenue_label = ttk.Label(frame, text=f"${self.__dashboard_data['Revenue']:.2f}", font=("Arial", 30), foreground="green")
        revenue_label.pack()



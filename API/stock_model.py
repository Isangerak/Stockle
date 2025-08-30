import sqlite3
from datetime import datetime


class DatabaseManager():
    # Handle all database operations
    def __init__(self,db_path):
        self.__db_path = db_path
    

    def run_sql_command(self,query,return_result=False,params=None):
        # Run SQL command given with params if any
        conn = sqlite3.connect(self.__db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA journal_mode=WAL;")
        if params == None:
            cursor.execute(query)
            conn.commit()
        else:
            cursor.execute(query,params)
            conn.commit()

        if return_result:
            results = cursor.fetchall()
            conn.commit()
            conn.close()

            # Returns a list of tuples
            return results
        else:
            conn.commit()
            conn.close()


    def run_sql_script(self,script):
        
        conn = sqlite3.connect(self.__db_path)
        cursor = conn.cursor()
        cursor.executescript(script)
        conn.commit()
        conn.close()


    def run_sql_many(self, query, params_list):
        # Run SQL param repeatedly with massive param list
        conn = sqlite3.connect(self.__db_path)
        try:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Database error: {e}")
        finally:
            conn.close()

class Product():
    def __init__(self, db):
        self.__db = db # Database Manager

    def return_stock(self, query=""):
        sql_query = """
            SELECT 
                Product.product_id, 
                Product.name, 
                Product.category, 
                COALESCE(independent_rule_group.rule_name, category_rule_group.rule_name) AS rule_name, 
                Product.quantity
            FROM Product
            LEFT JOIN RuleGroup AS independent_rule_group 
                ON Product.independent_rule_group_id = independent_rule_group.rule_group_id
            LEFT JOIN RuleGroup AS category_rule_group 
                ON Product.category_rule_group_id = category_rule_group.rule_group_id;"""
        # Search for all the products
        if query == "":
            # If query none then return all
            results = self.__db.run_sql_command(sql_query, True)
        else:
            # A search term was entered
            # Alter SQL Query
            new_query = sql_query[:-1] + """
             WHERE Product.name LIKE ? 
            OR Product.category LIKE ?  
            OR COALESCE(independent_rule_group.rule_name, category_rule_group.rule_name) LIKE ? 
            OR Product.quantity = ?;"""

            like_term = f"%{query}%"
            try:
                # See if query was for a quantity
                quantity_term = int(query)
            except ValueError:
                quantity_term = -1  # The search term was not a number 
            
            params = (like_term, like_term, like_term, quantity_term)
            
            results = self.__db.run_sql_command(new_query, True, params=params)
        
        return results



    def return_product_info(self,product_id):
        # Get product information for a given product_id
        query = f"""SELECT p.product_id, p.barcode,p.name, p.category,p.price_sell,p.vat,p.quantity,
        COALESCE(rg_independent.rule_name, rg_category.rule_name) AS active_rule_name
        FROM Product p
        LEFT JOIN RuleGroup rg_category ON p.category_rule_group_id = rg_category.rule_group_id
        LEFT JOIN RuleGroup rg_independent ON p.independent_rule_group_id = rg_independent.rule_group_id
        WHERE p.product_id = ?;"""
        product_info = self.__db.run_sql_command(query,True,params=(product_id,))
        # Configure results in dictionary for easy access once returned
        results = {
            "ID":product_info[0][0],
            "Barcode":product_info[0][1],
            "Name":product_info[0][2],
            "Category":product_info[0][3],
            "Selling Price":product_info[0][4],
            "VAT":product_info[0][5],
            "Quantity":product_info[0][6],
            "Rule":product_info[0][7]
        }

        return results



    def edit_product_quantity(self,new_values):
        # new values is a dictionary
        # product_id : quantity
        query = """
        UPDATE Product 
        SET quantity = ?
        WHERE product_id = ?;
        """
        # Create params list
        params = [(quantity, product_id) for product_id, quantity in new_values.items()]
        self.__db.run_sql_many(query, params)


class Rulegroup():
    def __init__(self, db):
        self.__db = db # Database Manager

    def get_rule_info(self,rule_id):
        # get rule info for given rule_id
        rule_info = {}
        query = f"SELECT rule_group_id,rule_name, category, min_stock FROM RuleGroup WHERE rule_group_id = ?;"
        results = self.__db.run_sql_command(query,True,params=(int(rule_id),))
        # Configure results into rule_info dictionary
        rule_info["ID"] = results[0][0]
        rule_info["Name"] = results[0][1]
        rule_info["Category"] = results[0][2]
        rule_info["Minimum Stock"] = results[0][3]
        # Retrive products that rule applied to if category is none
        if rule_info["Category"] == "None":
            query = f"SELECT product_id, name, category, quantity FROM Product WHERE ? = category_rule_group_id OR ? = independent_rule_group_id;" 
            params = (rule_id,rule_id)
            results = self.__db.run_sql_command(query,True,params=params)
            rule_info["Products"] = results
        return rule_info




    
            
    def return_rule_groups(self,query=""):
        # Return all rulegroups with / without query
        sql_query = """
            SELECT rule_group_id, rule_name,category,min_stock
            FROM RuleGroup
            WHERE rule_name LIKE ? OR category LIKE ?  OR min_stock=?;
            """
        # Return all rulegroups
        if query == "":
            sql_query = """
            SELECT rule_group_id, rule_name, category ,min_stock
            FROM RuleGroup;"""
            results = self.__db.run_sql_command(sql_query,True)
        else:
            like_term = f"%{query}%"
            try:
                # See if query was an integer to reference to quantity
                quantity_term = int(query)
            except ValueError:
                quantity_term = -1  # The search term was not a number 

            # Pass the formatted parameters
            params = (like_term, like_term, quantity_term)

            results = self.__db.run_sql_command(sql_query,True,params=params)
    
        return results



    def check_rulegroup_validity(self,new_rule,update=False):
        # It will return (Pass/Fail,Message)
        # Check Minimum stock is natural number
        try:
            num = int(new_rule["Minimum Stock"])
            if num < 0:
                return False,"Number Must be or above 0"
        except ValueError:
            return False,"Please Enter a Whole Number"

        
        current_names = self.__db.run_sql_command("SELECT rule_name FROM RuleGroup;",return_result=True)
        taken_names = [row[0] for row in current_names]
        # Check if rule name taken
        if new_rule["Name"] in taken_names:
            if update:
                if new_rule["Old Name"] != new_rule["Name"]:
                    return False,"Name Must be Unique"
            else:
                return False,"Name Must be Unique"
        
        # Check no overlapping products with another independent rule group
        if new_rule["Category"] == 'None':
           
            if len(new_rule["Product IDs"]) == 0:
                return False,'The Rulegroup Cannot govern over no Products'
            placeholders = ""
            for id in new_rule["Product IDs"]:
                placeholders += " ?,"
            

            query = f"SELECT product_id, name, rule_name FROM Product LEFT JOIN RuleGroup on RuleGroup.rule_group_id = Product.independent_rule_group_id WHERE product_id in ({placeholders[:-1]}) and independent_rule_group_id is NOT NULL"
           
            
            if update:
                query += " AND rule_group_id != ?;"

                overlapping_products = self.__db.run_sql_command(query,return_result=True,params=tuple(new_rule["Product IDs"]) + (new_rule["ID"],))
            else:
                overlapping_products = self.__db.run_sql_command(f"{query};",return_result=True,params=tuple(new_rule["Product IDs"]))
            
            # return error if there were any overlapping products
            if len(overlapping_products) > 0:
                message = "Products already belong to another Independant Rulegroup:\n"
                for product in overlapping_products:
                    message += f"{product[1]} with ID {product[0]} belongs to {product[2]}\n"
                return False,message
            
            else:
                return True,""
        
        else:
            if update:
                if new_rule["Category"] == new_rule["Old Category"]:
                    return True,""
            # See if the category is already governed
            current_categories = self.get_governed_categories()
            if new_rule["Category"] in current_categories:
                return False,'Category is already being Governed!'
            else:
                
                return True,""
            


    def create_rulegroup(self,category,rule_name,min_stock,product_ids=None):
        # Create rulegroup once passed the validity test
        query = "INSERT INTO RuleGroup (rule_name, category, min_stock) VALUES (?, ?, ?);"
        self.__db.run_sql_command(query, params=(rule_name, category, min_stock))
        result = self.__db.run_sql_command("SELECT rule_group_id FROM RuleGroup WHERE rule_name= ?;",params=(rule_name,),return_result=True)
        # Get the new created rule id to apply it to products / categories
        new_rule_id = [row[0] for row in result]
        new_rule_id = new_rule_id[0]
        # Apply to Products
        if category == "None":
            placeholders =""
            for id in product_ids:
                placeholders += " ?,"
            params = (int(new_rule_id),) + tuple(product_ids)
            self.__db.run_sql_command(f"UPDATE Product SET independent_rule_group_id = ? WHERE product_id in ({placeholders[:-1]});",params=params)
        else:
            self.__db.run_sql_command("UPDATE Product SET category_rule_group_id = ? WHERE category = ?;",params=(int(new_rule_id),category))
        


    def delete_rulegroup(self,rule_id):
        # Delete the rule group
        self.__db.run_sql_command("DELETE FROM RuleGroup WHERE rule_group_id = ?;",params=(int(rule_id),))

    

    def get_categories(self):
            # Retrieve all unique cateories
            categories = self.__db.run_sql_command("SELECT DISTINCT category FROM Product WHERE category IS NOT NULL;",return_result=True)
            result = [row[0] for row in categories]
            return result
    

    def get_governed_categories(self):
        # Retrieve all categories that are governed by other rulegroups
        goverened_categories = self.__db.run_sql_command("SELECT category FROM RuleGroup;",return_result=True)
        result = [row[0] for row in goverened_categories]
        return result
    


class Order():
    def __init__(self, db):
        self.__db = db # Database Manager


    def return_orders(self,query):
        # Return orders with / without a query
        sql_query = """
            SELECT `Order`.product_id, Product.name ,Product.quantity
            FROM `Order`
            LEFT JOIN Product on `Order`.product_id = Product.product_id
            WHERE Product.name LIKE ? OR quantity=?;
            """
        if query == "":
            sql_query = """
            SELECT `Order`.product_id, Product.name ,Product.quantity
            FROM `Order`
            LEFT JOIN Product on `Order`.product_id = Product.product_id;"""
            results = self.__db.run_sql_command(sql_query,True)
        else:
            like_term = f"%{query}%"
            try:
                quantity_term = int(query)
            except ValueError:
                quantity_term = -1  # The search term was not a number 

            # Pass the formatted parameters
            params = (like_term, quantity_term)

            results = self.__db.run_sql_command(sql_query,True,params=params)
    
        return results
    

class Analytics():
    def __init__(self, db):
        self.__db = db # Database Manager


    def get_day_revenue(self):
        # Resets everyday
        query = "SELECT SUM(s.amount_sold * p.price_sell) AS total_revenue FROM Sold s INNER JOIN Product p ON s.barcode = p.barcode WHERE DATE(s.date) = DATE('now');" 
        revenue = self.__db.run_sql_command(query,return_result=True)
        str_figure = revenue[0][0]
        if str_figure == None:
            return 0
        else:
            return int(str_figure)



    def get_worst_products(self):
        # Retrieve worst 10 selling products
        query = """SELECT 
            p.product_id,
            p.name,
            p.category,
            p.price_sell,
            SUM(s.amount_sold) AS total_sales
        FROM 
            Sold s
        INNER JOIN 
            Product p
        ON 
            s.barcode = p.barcode
        GROUP BY 
            p.name, p.barcode, p.category
        ORDER BY 
            total_sales ASC
        LIMIT 10;"""
        results = self.__db.run_sql_command(query,return_result=True)
        return results


    def get_categories_sales(self):
        query = "SELECT p.category, SUM(s.amount_sold) AS total_sales FROM Sold s INNER JOIN Product p ON s.barcode=p.barcode GROUP BY p.category;"
        results = self.__db.run_sql_command(query,return_result=True)
        return results




class StockAlert():
    def __init__(self, db):
        self.__db = db # Database Manager

    # Can return or clear stock alerts generated by operations
    def return_stock_alerts(self):
                query = "SELECT Product.name,message FROM stock_alerts LEFT JOIN Product on stock_alerts.barcode=Product.barcode;"
                results = self.__db.run_sql_command(query,return_result=True)
                return results
            
    def clear_stock_alerts(self):
        self.__db.run_sql_command("DELETE FROM stock_alerts;")




class BatchProcessor():
   def __init__(self, db):
        self.__db = db  # Database Manager


   def process_batch(self,batch):
        # Batch is already ordered on timeframe, from earliest to latest
        sales = []
        new_products = []
        edits = []
        deletes = []

        # Parse through the incoming data
        for entry in batch:
        
            if entry['Change Type'] == 'SALE':
                sales.append(entry)
            elif entry['Change Type'] == 'ADD':
                new_products.append(entry)
            elif entry['Change Type'] == 'EDIT':
                edits.append(entry)
            elif entry['Change Type'] == 'DELETE':
                deletes.append(entry)
                barcode = entry['Barcode']
                # Remove from edits
                edits = [product for product in edits if product['Barcode'] != barcode]
                # Remove from new_products
                new_products = [product for product in new_products if product['Barcode'] != barcode]




        # Process Deletes
        for delete in deletes:
            barcode = delete['Barcode']
            self.__db.run_sql_command("DELETE FROM Product WHERE Barcode=?;",params=(barcode,))
        

        # Process Additions
        for product in new_products:
            barcode = product['Barcode']
            name = product['Name']
            price = product['Price']
            category = product['Category']
            vat = product['VAT']
            self.__db.run_sql_command("INSERT INTO Product (barcode,name,category,price_sell,vat) VALUES (?,?,?,?,?);",params=(barcode,name,category,price,vat,))

        
        # Process Valid Edits
        for product in edits:
            barcode = product['Barcode']
            name = product['Name']
            price = product['Price']
            category = product['Category']
            vat = product['VAT']
        
            self.__db.run_sql_command("UPDATE Product SET barcode=?,name=?,category=?,price_sell=?,vat=? WHERE Barcode=?;",params=(barcode,name,category,price,vat,barcode,))

        # Process Sales
        for sale in sales:
            barcode = sale['Barcode']
            quantity = sale['Quantity']
            # Format date to represent original sales
            timeframe_str = str(sale['TimeFrame']) + "00"
            date_time = datetime.strptime(timeframe_str, "%Y%m%d%H%M%S")
            formatted_date = date_time.strftime("%Y-%m-%d %H:%M:%S")  
            self.__db.run_sql_command("INSERT INTO Sold (barcode,amount_sold,date) VALUES (?,?,?)",params=(barcode,quantity,formatted_date,))
            
    

class StockModel():
    # Interface for stock related management and operations
    def __init__(self, db_path: str = "API/Databases/stock_management.db"):
        db = DatabaseManager(db_path)
        self.products = Product(db)
        self.rules = Rulegroup(db)
        self.orders = Order(db)
        self.analytics = Analytics(db)
        self.alerts = StockAlert(db)
        self.process = BatchProcessor(db)

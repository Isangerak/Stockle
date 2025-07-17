import os
from flask import Flask, request, jsonify , make_response
import socket
from encryption import RSA, AES  
import json

import base64
from stock_model import *
from user_model import *
from setup import create_account, create_database
# --------------------------CONFIG -------------------------------
# Configure Public and Private key for API
rsa = RSA()

# Configure IP Table with Symmetric Session Keys
ip_table = {}



DATABASE_PATH = 'Databases/stock_management.db'

# Create the Initial Database records
if not os.path.exists("API/" + DATABASE_PATH):
    print("No Databases Found!")
    print("Creating Initial Databases Now ...")
    create_database()

if not os.path.exists("API/Databases/users.json"):
    print(""""
------------------------------------------------------
WELCOME TO STOCKLE BY KARAM SANGERA 
------------------------------------------------------
########
Default username: admin
Default password: admin
########
------------------------------------------------------
PLEASE CHANGE THESE CREDENTIALS AS SOON AS POSSIBLE
------------------------------------------------------""")
    create_account()

# Set up Models
user_model = UserModel()
stock_model = StockModel()

app = Flask(__name__)
# Set the flag for real time sync request
app.config['sync_now_flag'] = False

# ------------------ERROR HANDLING ------------------------------------
# Handle any unexcpted errors that come from the endpoints
def catch_errors(error_message="Error occurred", status_code=400):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # Run the original endpoint and if any errors occur trigger except block
                return func(*args, **kwargs)
                
            except Exception:
                # Return the error associated with the endpoint
                return jsonify({"error": error_message}), status_code
        wrapper.__name__ = func.__name__

        return wrapper
    return decorator

#----------------- DECRYPTION AND ENCRYPTION METHODS ---------------------------------------
@app.before_request
def validate_symmetric_key():
    # For testing stage explicitly

    # Skip validation and decryption if these endpoints
    if request.endpoint in ['status', 'connect']:
        return

    if request.endpoint in ['sync_now'] and request.method == "GET":
        return
    # Check user has session set up. If not deny access to client
    client_ip = request.remote_addr
    if client_ip not in ip_table:
        return jsonify({'error': 'Unauthorized: Symmetric key not established'}), 404

    # Skip  decryption if no data and a GET request
    if request.method == "GET" and not request.data:
        return

    # If there is data decrypt
    if request.json:
        try:
            # Set symmetric cipher object using the client designated symmetric key
            aes_cipher = AES(ip_table[client_ip])
            # Retrieve data from data wrapper
            request_data = request.json["Data"]
        
            base64bytes = request_data.encode('utf-8')
            decoded_data = base64.b64decode(base64bytes)
            decrypted_bytes = aes_cipher.decrypt(decoded_data)  
            plaintext = decrypted_bytes.decode('utf-8')
         
            try:
                # See if data was a dictionary, list, tuple
                data = json.loads(plaintext)
 
                
            except json.JSONDecodeError:
                # data was a plaintext and not dict, list, tuple
                data = plaintext
            
            
            # Set environemntal variable so it can be accessed by endpoints
            request.environ['Decrypted_json'] = data
            
        except Exception:
            return jsonify({'error': 'Invalid or improperly encrypted data'}), 400
    
@app.after_request
def encrypt_response(response):
    client_ip = request.remote_addr

    # Skip encryption for GET requests to 'status' and 'connect' endpoints
    if request.method == 'GET' and request.endpoint in ['status', 'connect','sync_now']:
        return response

    # Proceed with encryption if the client has a session key and the request is not GET
    if client_ip in ip_table and response.data:
        try:
            aes_cipher = AES(ip_table[client_ip])
            
            if  isinstance(response.data,str):
                encoded_data = response.data.encode('utf-8')
                encrypted_data = aes_cipher.encrypt(encoded_data)
            else:
                encrypted_data = aes_cipher.encrypt(response.data)

            data = base64.b64encode(encrypted_data)
            
            #Put in the Data Wrapper
            response_dict = {"Data":data.decode('utf-8')}
            response.set_data(json.dumps(response_dict)) 
            response.headers['Content-Type'] = 'application/json'

        except Exception as e:
            return make_response('Error encrypting response data', 500)

    return response




#----------------- STOCK MANAGEMENT ENDPOINTS ---------------------------------------
@app.route('/status', methods=['GET'])
# Check Status for API
def status():
    return 'API Ready for transfer', 200



@app.route('/sync_now', methods=['POST','GET'])    
# Set or get sync_now flag
def sync_now():
    if request.method == 'POST':
        # Trigger the sync now flag
        app.config['sync_now_flag'] = True
        return 'Sync Now Triggered',200

    elif request.method == 'GET':
        # Check if flag was triggered
        if app.config['sync_now_flag']:
            app.config['sync_now_flag'] = False
            return 'Ready To Sync',200
        else:
            return 'Not Triggered!',400
   




@app.route('/connect', methods=['GET', 'POST'])
def connect():
    #Endpoint for RSA handshake and symmetric key establishment
    # Retrieve Public Key
    if request.method == 'GET':
        return jsonify({'public_key': rsa.public_key}), 200
    # Send encrypted AES key
    elif request.method == 'POST':
        try:
            # Retrieve symmetric key from payload
            data = request.json
            encrypted_data = data["Data"]
            symmetric_key = rsa.decrypt(encrypted_data)
            
            # Validate AES key length
            if len(symmetric_key) != 32:
                return 'Invalid Symmetric Key Length', 400

            # Store the decrypted AES session key for that user valid
            ip_table[request.remote_addr] = symmetric_key
            return 'Symmetric key established', 200

        except Exception:
            return 'Invalid Ciphertext Provided', 400


@app.route('/login',methods=['POST'])
@catch_errors("Incorrect Data Inputted",400)
def login():
    # Send Login Credentials to get validated
    if request.method == "POST":
        data = request.environ['Decrypted_json']
        # See if credentials were valid
        valid = user_model.login(data["username"],data["password"])
        if valid:
            return user_model.get_user(data["username"]),200
        else:
            return 'Invalid or Incorrect Credentials',400
    


@app.route('/stock',methods=['GET',"PUT"])
@catch_errors("Incorrect Data Inputted",400)
def stock():
    if request.method == "GET":
        # Get search query for stock from data
        data = request.environ['Decrypted_json']
        stock = stock_model.products.return_stock(data['query'])
        return stock,200
        
    
    elif request.method == "PUT":
        # Update quatntiy of a product in the data
        data = request.environ['Decrypted_json']
        stock_model.products.edit_product_quantity(data['updated products'])
        return "Success",200


@app.route('/orders',methods=['GET'])
@catch_errors("Incorrect Data Inputted",400)
def orders():
    if request.method == "GET":
        # Get all stock Orders
        data = request.environ['Decrypted_json']
        stock = stock_model.orders.return_orders(data['query'])
        return stock,200
            

@app.route('/product_overview',methods=['GET'])
@catch_errors("Incorrect Data Inputted",400)
def product_overview():
    # Retrieve product overview for product_id given
    if request.method == "GET":
        data = request.environ["Decrypted_json"]
        product_data = stock_model.products.return_product_info(data)
        return product_data,200
        

@app.route('/rulegroups',methods=['POST','GET',"DELETE","PUT"])
@catch_errors("Incorrect Data Inputted",400)
def rulegroups():
    if request.method == "GET":
        # Get Rulegroups based off search provided
        data = request.environ["Decrypted_json"]
        search_result = stock_model.rules.return_rule_groups(data["query"])
        return search_result,200
     
    elif request.method == "POST":
        # Receive rulegroup that wishes to be created
        data = request.environ["Decrypted_json"]
        # Validate if rule can be created
        valid,message = stock_model.rules.check_rulegroup_validity(data)
        if valid:
            # Create rule
            if data["Category"] == "None":
                stock_model.rules.create_rulegroup(data["Category"],data["Name"],data["Minimum Stock"],data["Product IDs"])
            else:
                stock_model.rules.create_rulegroup(data["Category"],data["Name"],data["Minimum Stock"])

            return "Added Successfully",200
        else:
            return message,400
            
        
        
    elif request.method == "DELETE":
        # Delete a rulegroup with the given name
        rule_id = request.environ["Decrypted_json"]
       
        stock_model.rules.delete_rulegroup(rule_id)
        return "Deleted Successfully",200
      
    elif request.method == "PUT":
        # Update a rulegroup with new values
        data = request.environ["Decrypted_json"]
        # Validate if rule can be updated will new values
        valid,message = stock_model.rules.check_rulegroup_validity(data,update=True)
        if valid:
            # Delete old rule and add new updated rulegroup
            stock_model.rules.delete_rulegroup(data["ID"])
            if data["Category"] == "None":
                stock_model.rules.create_rulegroup(data["Category"],data["Name"],data["Minimum Stock"],data["Product IDs"])
            else:
                stock_model.rules.create_rulegroup(data["Category"],data["Name"],data["Minimum Stock"])
            return "Updated Sucessfully",200
        else:
            return message,400
        

@app.route('/rule_overview',methods=["GET"])
@catch_errors("Incorrect Data Inputted",400)
def rule_overview():
    if request.method == "GET":
        # Get information about a rulegroup 
        data = request.environ["Decrypted_json"]
        return stock_model.rules.get_rule_info(data["rule_id"]),200
       


@app.route('/categories',methods=['GET'])
@catch_errors("Incorrect Data Inputted",400)
def categories():
    # Retrieve and return all categories
    if request.method == "GET":
        return stock_model.rules.get_categories(),200
      


@app.route('/dashboard', methods=["GET"])
@catch_errors("Error retrieving dashboard data", 500)
def dashboard():
    if request.method == "GET":
        # Get dashboard data 
        dashboard_data = {}
        dashboard_data['Worst Products'] = stock_model.analytics.get_worst_products()
        dashboard_data['Revenue'] = stock_model.analytics.get_day_revenue()
        dashboard_data['Category Sales'] = stock_model.analytics.get_categories_sales()
        return dashboard_data,200
   



@app.route('/users',methods=['GET','POST','PUT','DELETE'])
@catch_errors("Incorrect Data Inputted",400)
def users():
    # Get user information from username provided
    if request.method == 'GET':
        if "Decrypted_json" in request.environ:
            data = request.environ['Decrypted_json']
            try:
                user = data['username']
                user_details = user_model.get_user(user)
                if user_details is None:
                    return "No User Exists",404
                else:
                    return user_details,200
            except Exception as e:
                return "Incorrect Data Given",400
        else:
            all_users = user_model.load_users()
            return all_users,200
       
    # Create a new user with information provided
    elif request.method == 'POST':
        data = request.environ['Decrypted_json']
      
        user_model.add_user(data)
        return "Added User",200
       
    # Delete a user
    elif request.method == 'DELETE':
        data = request.environ["Decrypted_json"]
        user_model.delete_user(data)
        return 'Successfully Deleted User',200
    
    # Update a user with new information
    elif request.method == 'PUT':
        data = request.environ["Decrypted_json"]
        user_model.update_user(data['old user'],data['new user'])
        return "Successfully Updated",200
    
      

@app.route('/change_password',methods=['POST'])
@catch_errors("Invalid Format",400)
def change_password():
    # Change password with new password
    if request.method == 'POST':
        data = request.environ["Decrypted_json"]
        # Update password for user with given hash
        success = user_model.change_password(data['username'],data['password_hash'])
        if success:
            return "Password Changed Successfully",200
        else:
            return "User does not exist for password change",404
        
       

@app.route('/stock_alerts',methods=['GET','POST'])
@catch_errors("Incorrect Data Provided",400)
# Retrieve (GET) or delete (POST) stock alerts from database
def stock_alerts():
    if request.method == 'GET':
        return stock_model.alerts.return_stock_alerts(),200
    elif request.method == 'POST':
        stock_model.alerts.clear_stock_alerts()
        return "Cleared Stock Alerts!",200
    else:
        return "Invalid Request",404
    
#----------------- BACKEND EXCLUSIVE ENDPOINTS  ---------------------------------------

@app.route('/process_data',methods=['POST'])
@catch_errors("Incorrect Data Given",400)
def process_data():
    # Get the JSON data directly
    if request.method == "POST":
        data = request.environ['Decrypted_json']  # This will get the whole JSON object
        # Check if the incoming data has the 'data' key and that it's a list
      
        if not isinstance(data, list):
            return 'Invalid data provided', 400
        # Process data
        stock_model.process.process_batch(data)
        return 'Data processed and stored successfully', 200
    


if __name__ == '__main__':
    hostname = socket.gethostname()
    ipv4_addr = socket.gethostbyname(hostname)
    app.run(host=ipv4_addr, port=5000)




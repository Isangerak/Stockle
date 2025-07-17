import requests
import base64
import json
import os
from encryption import RSA, AES  

# Api Controller for the till backend script - different to the inventories api controller
class APIController:
    def __init__(self, api_url):
        # Config for controller
        self.__api_url = api_url
        self.__rsa = RSA()  
        self.__aes = None  
        self.__session_key = None  
        self.__public_key = None  # Server's public key


    def __get_public_key(self):
        # Retrieve API's rsa public key
        try:
            response = requests.get(f"{self.__api_url}/connect")
            if response.status_code == 200:
               
                self.__public_key = response.json().get('public_key')
                return True
            else:
                print("Failed to retrieve public key.")
                return False
        except Exception as e:
            print(f"Error retrieving public key: {e}")
            return False

    def __establish_secure_connection(self):
        # Transfer over AES key that will be used for the transmission
        if not self.__public_key:
            if not self.__get_public_key():
                return False

        # Generate a symmetric session key (256-bit AES key)
        self.__session_key = os.urandom(32)
        self.__aes = AES(self.__session_key)

        # Encrypt the session key with the server's public RSA key
        encrypted_data = self.__rsa.encrypt(self.__session_key, self.__public_key)
        
    
        # Send the encrypted session key to the server
        try:
            response = requests.post(
                f"{self.__api_url}/connect",
                json={'Data': encrypted_data}
            )
            if response.status_code == 200:
                print("Secure connection established.")
                return True
            else:
                print("Failed to establish secure connection.")
                return False
        except Exception as e:
            print(f"Error establishing secure connection: {e}")
            self.__session_key = None
            return False

    def __encrypt_message(self, data):
        # data should be in bytes format
        if not isinstance(data,bytes):
            raise ValueError("Data is not formatted in bytes. Unable to Encrypt")
        
        if not self.__aes:
            raise ValueError("Secure connection not established.")
        

        # Encrypt data using AES

        encrypted_data = self.__aes.encrypt(data)
        #Base 64 encode it so that it can be put into data wrapper
        encoded_data = base64.b64encode(encrypted_data)
        return encoded_data.decode('utf-8')

    def __decrypt_message(self, encrypted_data):
        if not self.__aes:
            raise ValueError("Secure connection not established.")
        
        
        # Decrypt with AES
        base64bytes = encrypted_data.encode('utf-8')
        decoded_data = base64.b64decode(base64bytes)
        decrypted_bytes = self.__aes.decrypt(decoded_data)  
        plaintext = decrypted_bytes.decode('utf-8')
        try:
            # See if data was a dictionary, list, tuple
            data = json.loads(plaintext)
            return data
        except json.JSONDecodeError:
            # If not return the String
            return plaintext
        

    def send_request(self, endpoint, method='GET', data=None):
        try:
            # GET Request to the sync_now endpoint or status endpoint
            if method == "GET":
             
                response = requests.request(
                    method,
                    f"{self.__api_url}/{endpoint}",
                    headers={'Content-Type': 'application/json'},
                    timeout=5 
                )
                return  response.status_code

            else:
                #Send an encrypted request to the API and return the decrypted response
                if not self.__session_key:
                    if not self.__establish_secure_connection():
                        return False,404
                
                # Encrypt the request data if present
                if data:
                    if not isinstance(data,str):
                        data_str = json.dumps(data)
                        encoded_data = data_str.encode("utf-8")
                    else:
                        encoded_data = data.encode("utf-8")

                    encrypted_data = self.__encrypt_message(encoded_data)
                    response = requests.request(
                        method,
                        f"{self.__api_url}/{endpoint}",
                        json={"Data":encrypted_data},
                        headers={'Content-Type': 'application/json'}
                    )

              
                # Process Response
        
                    status_code = response.status_code
                    # Decrypt the response
                    response = response.json()
                    return self.__decrypt_message(response["Data"]), status_code
                
                else:
                    raise ValueError("NO DATA WAS PASSED TO SEND")
        # Api wasnt up when sending request
        except (requests.exceptions.RequestException , requests.exceptions.Timeout) :
            print("API is currently down, failed to send request")
            return False,404
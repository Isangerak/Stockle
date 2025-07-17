import requests
import base64
import json
import os
from encryption import RSA, AES  
import time 
import tkinter as tk
from tkinter import messagebox

class APIController:
    def __init__(self,api_url,app_controller):
        # Class to manage all api transcations from application
        # Set variables
        self.__api_url = api_url
        self.__rsa = RSA()  
        self.__aes = None  
        self.__session_key = None 
        self.__session_valid = False 
        # Variables for reconnection
        self.__max_retries = 5
        self.__current_retries = 0
        # App Controller
        self.__app_controller = app_controller
        self.__public_key = None  # Server's public key

    def __exponential_backoff(self):
        # Backoff timer similiar to CSMA CA. Prevents redundant multiple api calls
        delay = min(2 ** self.__current_retries, 32)
        start_time = time.time()
        while time.time() - start_time < delay and not self.__app_controller.app_shutdown:
            # Sleep for small amount to allow for main view to process showing overlay frame. 
            time.sleep(0.1)
            try:
                self.__app_controller.update_overlay()
            except tk.TclError:
                # Main view destroyed; exit loop and stop calling api
                break
        self.__current_retries += 1

    def __get_public_key(self):
        # Get the public key of the api 
        try:
            response = requests.get(f"{self.__api_url}/connect",timeout=10)
            if response.status_code == 200:
               # Retrieval was successfull
                self.__public_key = response.json().get('public_key')
                return True
            else:
                print("Failed to retrieve public key.")
                return False
        except requests.exceptions.RequestException:
            return False


    def establish_secure_connection(self):
        # Transfer symmetric key that the api_controller sets up and transfer it to APi using its public key
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
                # Transaction was successful
                print("Secure connection established.")
                self.__session_valid = True
                return True
        except requests.exceptions.RequestException:
            # API was not able to be reached
            self.__session_valid = False
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
        # Decrypt incoming data from the api
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
        #Send an encrypted request to the API and return the decrypted response
        # loop to make sure request isnt infinitely sent repeatedly and has a breakpoint
        while self.__current_retries < self.__max_retries and not self.__app_controller.app_shutdown:
            try:
                # Either a new api instance or an error occured on API side requiring new session to be created
                if not self.__session_valid:
                    self.establish_secure_connection()
                    # Only show overlay and backoff timer if the program shows the main_view
                    if self.__app_controller.app_status():
                        self.__app_controller.handle_api_failure()
                        self.__exponential_backoff()
                    # Loop again through the function
                    continue
        
                # Encrypt the request data if present
                if data:
                    if not isinstance(data,str):
                        data_str = json.dumps(data)
                        encoded_data = data_str.encode("utf-8")
                    else:
                        encoded_data = data.encode("utf-8")

                    encrypted_data = self.__encrypt_message(encoded_data)
                    # Send data to set endpoint specified
                    response = requests.request(
                        method,
                        f"{self.__api_url}/{endpoint}",
                        json={"Data":encrypted_data},
                        headers={'Content-Type': 'application/json'}
                    )
                

                else:
                    # No data in payload, dont add a data portion in the payload
                    response = requests.request(
                        method,
                        f"{self.__api_url}/{endpoint}",
                        headers={'Content-Type': 'application/json'}
                    )

                # Process Response
                if response.status_code == 404 and "Symmetric key" in response.text:
                    # Deined access to api because invalid symmetric key session. Need to create new session and resend 
                    self.__session_valid = False
                    self.__public_key = None

                    # Skip remaining code and restart loop
                    continue
                # Response was a valid response with a data wrapper
                else:
                    status_code = response.status_code
                    # Decrypt the response
                    response = response.json()
                    # Reset current retries as transaction was successful
                    self.__current_retries = 0
                    # Dont handle reconnection process if there is no main_view to perform it on
                    if endpoint != "login":
                        self.__app_controller.handle_api_reconnection()
                    return self.__decrypt_message(response["Data"]), status_code
                
            except requests.exceptions.RequestException:
                # Dont perform overlay operations if main_view doesn't exist
                if not self.__app_controller.app_status():
                    messagebox.showerror("API Unaivalable","Please Try Again Later")
                    return False,404
                else:
                    self.__app_controller.handle_api_failure()
                    self.__exponential_backoff()
                continue
        if self.__app_controller.app_shutdown:
            # Return None message and 0 status code  because app is already closed
            raise ConnectionError("API unavailable after multiple retries. check up on API")

        # Reset and show api failure
        self.__current_retries = 0
        self.__app_controller.handle_api_failure(max_retries=True)
        raise ConnectionError("API unavailable after multiple retries. check up on API")
                

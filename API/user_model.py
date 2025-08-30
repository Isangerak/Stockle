import json
from HashAlgorithm import SHA1


class UserModel():
    def __init__(self,file_path):
        self.__file_path = file_path
        # Load all users into variable
        self.__user_data = self.load_users()
        # Set hash algorithm for local use
        self.hash = SHA1()



    def login(self, username,password):
        # Check if username is valid 
        # Return if the login details were valid 
        for user in self.__user_data:
            if user["username"] == username:
                if password == user["password_hash"]:
                    return True
        return False
    

    def load_users(self):
        # Load data from JSON
        with open(self.__file_path,"r") as file:
            data = json.load(file)
            return data

    def add_user(self,new_user):
        # Add user to JSON file
        self.__user_data.append(new_user)
        self.update_users()

        
    def update_users(self):
        # Write up new data in JSON
        with open(self.__file_path,"w") as file:
            json.dump(self.__user_data,file,indent=4)


    def get_user(self,username):
        # Get user with username given
        for user in self.__user_data:
            if user["username"] == username:
                return user
        # User did not exist
        return None 
    
    def delete_user(self,username):
        # Delete user with given username
        self.__user_data = [user for user in self.__user_data if user["username"] != username]
        self.update_users()



    def update_user(self,old_user,new_user):
        # Delete and renew user with new credentials
        self.delete_user(old_user)
        self.add_user(new_user)


    def change_password(self,username,password_hash):
        # Change password with new password hash
        user = self.get_user(username)
        if user is not None:
            user["password_hash"] = password_hash
            self.update_users()
            return True
        else:
            return False

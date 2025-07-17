from views.user_view import *
from HashAlgorithm import SHA1


# Controller to handle all user related api call formats and user frame management
class UserController:
    def __init__(self, api_controller,app_controller):
        self.__api_controller = api_controller
        self.app_controller = app_controller
        # All frames controlled under the controller
        self.frames = {
            "Add User":AddUserFrame,
            "Show Users":ShowUsersFrame,
            "User Details":ShowUserDetailsFrame,
        }

    def get_frame(self, frame_name, parent,*args):
        # Pass arguments to frame if any were passed
        if frame_name in self.frames:
            if args:
                return self.frames[frame_name](parent,self,args)
            return self.frames[frame_name](parent, self)
        else:
            raise ValueError(f"Frame {frame_name} does not exist")




    def convert_password(self,password):
        # Convert pasword to a hash
        sha = SHA1()
        password_hash = sha.hash(password,hex=True)
        return password_hash


   

    def login(self, username, password):
        # Format login credentials and send over to /login endpoint
        # Set app_shutdown to False in case in case of relogin
        self.app_controller.app_shutdown = False
        sha = SHA1()
        hashed_password = sha.hash(password,hex=True)
        response,status_code = self.__api_controller.send_request(
            endpoint="login",
            method='POST',
            data={'username': username, 'password': hashed_password}
        )
        if response and status_code == 200:
            # User was valid send back a success
            self.app_controller.set_current_user(response) 
            return True
        # user was not valid
        return False


    def get_users(self):
        #Retrieve a list of all users
        response,status_code = self.__api_controller.send_request(
            endpoint="users",
            method='GET'
        )
        if status_code == 200:
            return response
        else:
            return {}
        
    def get_user(self, username):
        # Get user details with username given
        response,status_code = self.__api_controller.send_request(
            endpoint="users",
            method='GET',
            data={'username': username}
        )
        if status_code == 200:
            return response
        elif status_code == 404:
            return ""
        else:
            None

        
    def change_password(self, username, password_hash):
        _,status_code = self.__api_controller.send_request(
            endpoint="change_password",
            method='POST',
            data={'username': username, 'password_hash': password_hash}
        )
        if status_code == 200:
            return True
        else:
            return False
    


    def check_username(self,username):
        # Ensure username is valid and not empty
        user = self.get_user(username)
        if user != "" or username == "":
            return False
        else:
            return True

     
    def check_password(self, password):
        # Ensure password conforms to having 1 spec, upper / lower, 1 num, and 10+ char
        special_chars = "!£$%^&*()_-+=?"
        numbers = "0123456789"
        if len(password) < 10:
            return False, "Password must have a length of 10+ characters"

        special_pass = any(c in special_chars for c in password)
        number_pass = any(c in numbers for c in password)
        upper_pass = any(c.isupper() for c in password)
        lower_pass = any(c.islower() for c in password)

        if not special_pass:
            return False, f"Require at least 1 special character. Allowed characters: {special_chars}"
        if not number_pass:
            return False, "Requires at least 1 numerical character"
        if not upper_pass or not lower_pass:
            return False, "Password Needs a mix of Upper and Lower case characters"

        return True, ""

    def update_user(self, old_user,new_user):
        _,status_code = self.__api_controller.send_request(
            endpoint="users",
            method='PUT',
            data={'old user':old_user,'new user':new_user}
        )
        if status_code == 200:
            if old_user == self.app_controller.get_current_user('username'):
                self.app_controller.set_current_user(new_user) 
            return "Updated Successfully"
        else:
            return "Updating User Failed, API Busy or Unavailable"
        
    

    def add_user(self, user):
        #Add a new user
        response,_ = self.__api_controller.send_request(
            endpoint="users",
            method='POST',
            data=user
        )
        return response

    def delete_user(self, username):
        #Delete a user
        response = self.__api_controller.send_request(
            endpoint="users",
            method='DELETE',
            data=username
        )
        return response    




    def logout(self):
        # Reset values and close main_view
        self.app_controller.current_user = None
        self.app_controller.app_shutdown = False
        
        

    def start(self):
        # Show login Page
        window = login_page(self)
        window.mainloop()
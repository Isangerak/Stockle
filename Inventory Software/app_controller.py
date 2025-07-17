class AppController:
    # Creates clear pathway to retrieve functions from another object
    # Reduces the chaining 
    def __init__(self, main_view):
        self.main_view = main_view
        self.__current_user = None
        self.app_shutdown = False

       
    def get_unsaved_changes(self):
        return self.main_view.unsaved_changes
        
    def set_unsaved_changes(self, value):
        self.main_view.unsaved_changes = value
        
    def show_user_frame(self, frame_name, *args):
        self.main_view.user_show_frame(frame_name, *args)
        
    def show_stock_frame(self, frame_name, *args):
        self.main_view.stock_show_frame(frame_name, *args)


    def authenticate(self,permission):
        # See fi uer is authenticated for the permission passed
        if self.__current_user and permission in self.__current_user["permissions"]:
            return True
        else:
            return False

    def clear_current_user(self):
        self.__current_user = None
    
    def set_current_user(self,user):
        self.__current_user = user

    def get_current_user(self,field=None):
        # Retrieve user details for the field given, if None retrieve the entire user
        if field != None:
            return self.__current_user[field]
        else:
            return self.__current_user
        
    def app_status(self):
        # See if the app is initialized
        if self.main_view:
            return True
        else:
            return False


    def handle_api_failure(self, max_retries=False):
        # Show the main_view overlay or api failure screen if max retries
        if not self.app_shutdown:
            if max_retries:
                self.main_view.show_fatal_error()
            else:
                self.main_view.show_overlay()

    def handle_api_reconnection(self):
        # Clear the overlay if the app still exists
        if not self.app_shutdown:
            self.main_view.remove_overlay()

    def update_overlay(self):
        # Update the overlay so that the progress bar can keep moving and stop freezing
        if self.main_view is not None:
                self.main_view.update_idletasks()
                self.main_view.update()
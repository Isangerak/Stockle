
from user_controller import UserController
from stock_controller import StockController
from api_controller import APIController
from views.main_view import TkinterApp
from app_controller import AppController
from tkinter import messagebox
import os

# API SOCKET SHOULD BE STATIC IPV4 ADDRESS
api_socket = "http://192.168.0.17:5000"
STOCKLE_IMG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Stockle.png")
SYNC_IMG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"sync.png")

def main():
    # Set Controllers
    app_controller = AppController(None) # Main View does not exist yet. Should be initiliazed once passed login page
    api_controller = APIController(api_socket,app_controller)
    user_controller = UserController(api_controller,app_controller)
    stock_controller = StockController(api_controller,app_controller)
    # See if Api is available before showing login page
    while True:
        if app_controller.app_shutdown:
            break
        
        if not api_controller.establish_secure_connection():
            messagebox.showerror("API unavailable","Please Try Again Later")
            break
        # Login Page
        user_controller.start()
        # Run main GUI if user logs in
        if app_controller.get_current_user() is None:
            break
    
        while app_controller.get_current_user() is not None:
            # Start app
            app = TkinterApp(user_controller,stock_controller,app_controller,STOCKLE_IMG_PATH,SYNC_IMG_PATH)
            # Set main_view for app_controller
            app_controller.main_view = app
            app.protocol("WM_DELETE_WINDOW",app.on_closing)
            app.mainloop()
        


# Start program
if __name__ == "__main__":
    main()




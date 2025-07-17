from HashAlgorithm import SHA1
import requests
import pickle
import sqlite3
import time 
import threading 
from datetime import datetime
import sqlite3
from api_controller import APIController






# ---------------------------- NODE CLASS FOR QUEUE --------------------------------
class Node():
    def __init__(self,data):
        self.data = data 
        self.next = None

# -----------------------------------------------------------------------------------

# -------------------------- THE 3 MAIN DATASTRUCTURES FOR BACKEND ----------------
class HashTable():
    def __init__(self,product_change_log,capacity=10,max_load_factor = 0.75,min_load_factor = 0.25):
        self.__change_log = product_change_log
        # Variables for dynamic resizing as database gets larger
        self.__max_load_factor = max_load_factor
        self.__min_load_factor = min_load_factor
        self.file_path = 'hashtable.pkl'
        self.__capacity = capacity
        self.__size = 0
        self.__buckets = [{} for i in range(self.__capacity)]
        # Load initial data if there was any before
        self.__load_data()
        self.__sha1 = SHA1()

    

    def save(self):
        # Write data into pickle file
        with open(self.file_path,'wb') as file:
            pickle.dump(self,file)



    def __load_data(self):
        try:
            # Try loading the pickle file and initializing variables if it exists
            with open(self.file_path,'rb') as file:
                loaded = pickle.load(file)

                # update attributes
                self.__max_load_factor = loaded.__max_load_factor
                self.__min_load_factor = loaded.__min_load_factor
                self.__capacity = loaded.__capacity
                self.__size = loaded.__size
                self.__buckets = loaded.__buckets
        except FileNotFoundError:
            return


    def __get_load_factor(self):
        # Return the proportion that the hashtable is full
        return self.__size / self.__capacity
    

    def __resize(self):
        # Resize to make it bigger 
        print("Resizing...")
        old_buckets = self.__buckets
        old_capacity = self.__capacity
        self.__capacity = old_capacity * 2
        self.__buckets = [{} for i in range(self.__capacity)]
        self.__size = 0

        # Rehash all existing items
        for bucket in old_buckets:
            for key,value in bucket.items():
                self.__insert(key,value)



    def __shrink(self):
        # Shrink if proportion of items fall below min_load_factor
        print("__shrinking")
        old_buckets = self.__buckets
        old_capacity = self.__capacity
        self.__size = 0
        self.__capacity = old_capacity // 2
        self.__buckets = [{} for i in range(self.__capacity)]
        
        # Rehash all existing items
        for bucket in old_buckets:
            for key,value in bucket.items():
                self.__insert(key,value)



    def __convert_to_key(self,product):
        # Takes in Dictionary and return Barcode
        return product["Barcode"]


    def __hash(self,key):
        # Hash the key (Barcode) and then mod the int hash value to find bucket index to store
        key_str = key.encode()
        hash_object = self.__sha1.hash(key_str,hex=True)
        # Convert Hash value into an integer
        hash_value = int(hash_object,16)

        # Make sure that the bucket its stored at is within 0:capcacity:-1
        return hash_value % self.__capacity




    def __insert(self,key,value):
        # This function will insert and edit, and return the change_id
        #Check if we need increase capacity first
        if self.__get_load_factor() > self.__max_load_factor:
            self.__resize()

        # No need to worry about collision avoidance as we are working with dictionaries now, not linked lists
        bucket_index = self.__hash(key)
        bucket = self.__buckets[bucket_index]

        # Check if the product is in the hashtable
        if key not in bucket:
            self.__size += 1
            bucket[key] = value
            return "ADD"

        # Check if values is edited    
        elif bucket[key] != value:
            bucket[key] = value
            return "EDIT"
            
        else:
            return None
        




    def __remove(self,key):
        # Remove from the hash table if they have passed key
        # Find bucket first
        bucket_index = self.__hash(key)
        bucket = self.__buckets[bucket_index]
        # Find item in the bucket and remove
        if key in bucket:
            del bucket[key]
            self.__size -= 1
            # Check if the capacity needs to be shrunk
            if self.__get_load_factor() < self.__min_load_factor:
                self.__shrink()
            return "DELETE"
        
        else:
            return None
           
            


    def update(self,db_data):
        # Updating from db_data: where configured as dictionaries
        current_keys = []
        for product in db_data:
     
            key = self.__convert_to_key(product)
            current_keys.append(key)
            # Try inserting
            change_id = self.__insert(key,product)
            # Add appropriate change tag and pass it to the change_log
            if change_id in ["ADD","EDIT"]:
                self.__change_log.add(product,change_id)
        # Remove items that are not in the database anymore
        for bucket in self.__buckets:
            for key in list(bucket.keys()):
                if key not in current_keys:
                    change_id = self.__remove(key)
                    # Add it to the change_log so it can delete the copy on the API's database
                    if change_id == "DELETE":
                        self.__change_log.add({'Barcode':key},change_id)
   





class Change_log():
    def __init__(self):
        # Config for change log
        self._log = []
        self.__file_path = 'change_log.pkl'
        self._sales_last_synced = None
        # load initial data
        self.__load_data()

    
    # Merge sort based on the time frame
    def time_frame_sort(self,arr):
        length = len(arr)
        # No need to merge sort if list empty or only 1 item in it
        if length > 1 :
            midpoint = length //2
            left_arr = arr[:midpoint]
            right_arr = arr[midpoint:]

            # Call the recursion until in array of 1
            self.time_frame_sort(left_arr)
            self.time_frame_sort(right_arr)

            # Merge Step
            i = 0 # left array index
            j = 0 # right array index
            k = 0 # merged array index
            while i < len(left_arr) and j < len(right_arr):
                if left_arr[i]['TimeFrame'] < right_arr[j]['TimeFrame']:
                    arr[k] = left_arr[i]
                    i += 1
                else:
                    arr[k] = right_arr[j]
                    j += 1
                k += 1

            # Consider case where left array never gets appeneded and theres nothing  in the right array anymore
            while i < len(left_arr):
                arr[k] = left_arr[i]
                i += 1
                k += 1

            # Consider Vice Versa
            while j < len(right_arr):
                arr[k] = right_arr[j]
                j += 1
                k += 1



    def save(self):
        # Save into the file path
        with open(self.__file_path,'wb') as file:
            pickle.dump(self,file)


    def __load_data(self):
        # Load data if there was any to load from
        try:
            with open(self.__file_path,'rb') as file:
                loaded_table = pickle.load(file)
                # update attributes
                self._log = loaded_table._log
           
                self._sales_last_synced = loaded_table._sales_last_synced

        except FileNotFoundError:
            return


    def add(self,product,change_type):
   
        # Need to add to the product the timestamp of the change and the change_type
        # store timeframe as an intenger so it can be merge sorted, API turns it back into normal timeframe afterwards only if its a sale
        if change_type == "DELETE":
            product["Change Type"] = change_type
            product["TimeFrame"] = 0
            self._log.append(product)
        else:
            shortened_timeframe = product['TimeFrame'][:16]
            dt = datetime.strptime(shortened_timeframe, "%Y-%m-%d %H:%M")

            # Format the datetime object to int
            timeframe_int = int(dt.strftime("%Y%m%d%H%M"))
            product_entry = {
                "Barcode": product["Barcode"],
                "Name": product["Name"],
                "Price": product['Price'],
                "VAT": product['VAT'],
                "Category": product['Category'],
                "Change Type": change_type,
                "TimeFrame": timeframe_int
            }
            # Add the new configured entry into the change log
         
            self._log.append(product_entry)
            
            



    def add_sales(self,sales_list):
        # Where sales_list is a list of dictionaries to be appended
        # Sales list should have each dictionary have a key value of change_id: "SALE"
        self._log = self._log + sales_list
        


    def remove(self,no_items):
        # Remove the number of items at the begininning of list. Where self._log is already sorted
        self._log = self._log[no_items:]
       

    def return_batch(self,batch_size=30):
        # return items for batch sending to API
        return self._log[:batch_size]
    
    def get_sales_last_synced(self):
        # Needed for knowing what sales to get instead of getting all of them again
        return self._sales_last_synced

    def update_sales_last_synced(self,timestamp):
        self._sales_last_synced = timestamp




class BatchQueue():
    def __init__(self,capacity=90,batch_size=30,file_path="batch_queue.pkl"):
        # This queue will by default be able to store 3 batches worth of updates
        self.__size = 0
        self.capacity = capacity
        self.__batch_size = batch_size
        self.__file_path = file_path
        self.__tail = None
        self.__head = None
        self.load_data()
        


    def is_empty(self):
        return self.__head is None
    

   

    def enqueue(self,data):
        # Add item to queue
        new_node = Node(data)
        # check if queue is empty
        if self.is_empty():
            # Set item to be the head and tail
            self.__head = self.__tail = new_node
        
        else:
            # add it to list
            self.__tail.next = new_node
            self.__tail = new_node
       

        # Increment Size
        self.__size += 1
        return True
        

    def get_batch(self):
        # Get n number of items from the front of queue. sepecified as batch_size. Doesnt actually remove it though
        batch = []
        if self.is_empty():
            return batch

        current_node = self.__head
        # Retrieve the items 
        while current_node is not None and len(batch) < self.__batch_size:
            batch.append(current_node.data)
            current_node = current_node.next
        return batch



    def dequeue_batch(self):
        # Remove item from queue
        count = 0
        
        if self.is_empty():
            return count
            
        

        current_node = self.__head
        while current_node is not None and count < self.__batch_size:
            current_node = current_node.next
            count += 1
            self.__size -= 1
        # Break the link from the front of the queue and set new head
        self.__head = current_node
        if self.__head == None:
            self.__tail = None
        return count



    def save(self):
        # Save it to specified path
        with open(self.__file_path,'wb') as file:
            pickle.dump(self,file)



    def load_data(self):
        # Load data if there was any to begin with
        try:
            with open(self.__file_path,'rb') as file:
                loaded_table = pickle.load(file)
                # update attributes
                self.__size = loaded_table.__size
                self.capacity = loaded_table.capacity
                self.__batch_size = loaded_table.__batch_size

                self.__tail = loaded_table.__tail
                self.__head = loaded_table.__head
              
        # File never existed
        except FileNotFoundError:
            return




class DatabaseManager():
    def __init__(self,db_location):
        self.__db = db_location

    
    def __convert_tuple_to_dict(self,product_tuple):
        return {
            "Barcode":product_tuple[0],
            "Name":product_tuple[1],
            "Price":product_tuple[2],
            "VAT":product_tuple[3],
            "Category":product_tuple[4],
            "TimeFrame":product_tuple[5]
        }


    def return_products(self):
        conn = sqlite3.connect(self.__db)
        # Query gets Barcode, Name, Price, VAT, Category
        cursor = conn.cursor()
        # Was short handed so doesn't take as much space, needed to be tested in cmd which also had a limit
        # Query is specific to Aronium as its a prototype
        query = """
        SELECT b.Value,p.Name,p.Price,t.Rate,pg.Name,p.DateUpdated
        FROM Barcode b LEFT JOIN Product p ON b.ProductId=P.ID
        LEFT JOIN ProductGroup pg ON p.ProductGroupId=pg.Id
        LEFT JOIN ProductTax pt ON p.Id=pt.ProductId 
        LEFT JOIN Tax t ON pt.TaxId=t.Id 
        WHERE Value is not NULL;"""
    
        cursor.execute(query)
        product_tuple = cursor.fetchall()
        conn.close()
        # Convert tuple results into a list of dictionaries
        product_result = [self.__convert_tuple_to_dict(product) for product in product_tuple]
        return product_result


    def return_sales_data(self,last_synced=None):
        sales_data = []
        # Get all products from the last synced to present, or return all if first time performing
    

        conn = sqlite3.connect(self.__db)
        cursor = conn.cursor()

        # Query for Aronium:
        # It gets the Barcode, Quantity, Date of Sale (2024-10-04 14:24:48.1000) format
        query = """
        SELECT Barcode.Value, DocumentItem.Quantity, Document.StockDate 
        FROM DocumentItem 
        INNER JOIN Document ON DocumentItem.DocumentId = Document.Id 
        INNER JOIN (
            SELECT ProductId, MAX(Value) as Value 
            FROM Barcode 
            GROUP BY ProductId
        ) AS Barcode ON DocumentItem.ProductId = Barcode.ProductId 
        WHERE Document.StockDate > ? 
        ORDER BY Document.StockDate;
        """

        # Return all products
   
        if last_synced==None:
            cursor.execute(query,("1970-01-01 00:00:00",))
        # Return set sales after time period
        else:
            cursor.execute(query,(last_synced,))

        products = cursor.fetchall()
        conn.close()

        # Set timeframe to get last timeframe from table
        timeframe = ""
        # Convert each sale's time of sale into an integer so that change_log can actually merge sort it
        for item in products:
            #2024-10-04 14:24:48.1000 - only want up to minutes so will split string
            timeframe=item[2]
            shortened_timeframe = timeframe[:16]
            dt = datetime.strptime(shortened_timeframe, "%Y-%m-%d %H:%M")

            # Format the datetime object to int
            timeframe_int = int(dt.strftime("%Y%m%d%H%M"))
            sales_data.append(
                {"Barcode":item[0],
                    "Quantity":item[1],
                    "Change Type":"SALE",
                    "TimeFrame":timeframe_int
                    }
                )
       
    
        # Return List and last synced time
        return sales_data , timeframe





# --------------------------------- CENTRALISED MANAGER FOR BOTH SYNC THREADS ---------------------------------
class SyncManager():
    def __init__(self,api_client,hashtable,change_log,queue_manager,db_manager,periodic_timer=3600,sync_now_timer=60):
        # Sleep Timers for both syncs
        self.__periodic_timer = periodic_timer
        self.__sync_now_timer = sync_now_timer
        # Initializing objects for the sync_manager to use
        self.__change_log = change_log
        self.__api_client = api_client
        self.__hashtable = hashtable
        self.__queue_manager = queue_manager
        self.__db_manager = db_manager

        # Theading Attributes
        self.__sync_lock = threading.Lock()
        self.__condition = threading.Condition()
        self.__current_syncing = None # Track which thread is currently syncing

    
    def __sync_api(self):
        print("SYNCING WITH API")
        # This is the function both syncs will run if the api is available (periodic) or the sync_now flag is active(listen_to_sync)
        # Trigger lock to other thread
        with self.__sync_lock:
            # Get sales and update last_synced
            if self.__change_log.get_sales_last_synced() == None:
                sales_change_list, sales_last_synced = self.__db_manager.return_sales_data()  # Fetch sales data
            else:
                sales_change_list, sales_last_synced = self.__db_manager.return_sales_data(self.__change_log.get_sales_last_synced())  # Fetch sales data
            
            if sales_last_synced != "":
                self.__change_log.update_sales_last_synced(sales_last_synced)
            # Add Sales and sort change_log ready for batch adding
            self.__change_log.add_sales(sales_change_list)
            self.__change_log.save()
            
            # Merge sort based on time frame
  
            self.__change_log.time_frame_sort(self.__change_log._log)

            # Where success is if the API is still up and ready to take data
            success = True
            # Keep sending API data if its available and queue is not empty
            while success == True:
                # Check if the queue is empty 
                if self.__queue_manager.is_empty():
                    
                    # Try to fill the queue
                    batch = self.__change_log.return_batch(batch_size = self.__queue_manager.capacity)
                    batch_len = len(batch)
                    # Consider the case where there is no more data in the change_log
                    if len(batch) == 0:
                        print("There is nothing to send")
                        break # End the data transmission
                    
                    # There is data in change_log so fill up entire queue again
                    else:
                        for product in batch:
                            self.__queue_manager.enqueue(product)
                            # Do not have to worry about it being over capacity as batch size is Equal or smaller than capacity
                        self.__change_log.remove(batch_len)
                        self.__change_log.save()
                        self.__queue_manager.save()
        
                #Clear the Batch Queue - could be leftover queue from last session or jsut recent addition
                else:
                    print("Clearing old queue...")
                    data = self.__queue_manager.get_batch() 
                    # Overwrite success with current availability
                    print("Sending Batch to api Client")
                    success = self.__api_client.send_batch(data)
                    if  success:
                        self.__queue_manager.dequeue_batch()
                        self.__queue_manager.save()
                

            self.__condition.notify_all()



    def __periodic_sync(self):
        # The interval can be changed: periodic_timer
        # Reset __periodic_sync timer if sync_now was pressed
        while True:
            with self.__condition:
                # Other sync is in operation with sending data with API
                while self.__current_syncing == "sync_now":
                    print("Periodic Sync: Waiting due to Sync Now Priority")
                    self.__condition.wait()
                
        
                # Update hashtable with data gotten from database
                db_data = self.__db_manager.return_products()
                self.__hashtable.update(db_data)
                self.__hashtable.save()
                self.__change_log.save()
                print("Periodic Sync Checking availability...")
                available = self.__api_client.check_availability()
                # if API up begin sync process
                print(f"Availability: {available}")
                if available:
                    print("Periodic Sync: API available")
                    self.__current_syncing = "__periodic_sync"
                    self.__sync_api()
                    # After transaction reset current syncing
                    self.__current_syncing = None 
                else:
                    print("Periodic Sync: API unavailable, retrying in next cycle")
            time.sleep(self.__periodic_timer)  # Normal periodic sleep
            
          
    
    def __listen_for_sync(self):
        # Sync for checking the button 
        while True:
            with self.__condition:
                # Dont start if other thread is syncing with the API
                while self.__current_syncing == "__periodic_sync":
                    self.__condition.wait()
          
                # Check if API has the sync_now flag active

                available = self.__api_client.check_sync_request()
                if available:
                    print("Sync Now: API available")
                    self.__current_syncing = "sync_now"
                    # actual operations
                    db_data = self.__db_manager.return_products()
                    self.__hashtable.update(db_data)
                    self.__hashtable.save()
                    self.__change_log.save()

                    self.__sync_api()
                    self.__current_syncing = None
                    print("Sync Now: Finished, periodic sync will sleep first")
                else:
                    print("Sync Now: API unavailable, retry in next cycle")

            time.sleep(self.__sync_now_timer)  # Normal "Sync Now" sleep

        



    def start(self):
        # Setting up threads for the different syncs
        periodic_thread = threading.Thread(target=self.__periodic_sync, name="PeriodicSyncThread")
        sync_now_thread = threading.Thread(target=self.__listen_for_sync, name="SyncNowThread")
        # Begin them
        periodic_thread.start()
        sync_now_thread.start()



# -------------------------------- API CLIENT TO FORMAT THE REQUESTS ---------------------------------------------------
        
class ApiClient():
    def __init__(self,api_socket):
        self.__controller = APIController(api_socket)

    def check_availability(self):
        try:
            # dont require response 
            status_code = self.__controller.send_request(
                endpoint="status",
                method="GET"
            )
   
            if status_code == 200:
                return True
            else:
                return False
           
        except requests.exceptions.ConnectionError:
            return False
        
    
    def check_sync_request(self):
        try:
            status_code = self.__controller.send_request(
                endpoint="sync_now",
                method="GET"
            )
            if status_code == 200:
                print("Software Is requesting Sync... Getting Ready")
                return True
            else:
                return False
        except requests.ConnectionError:
            return False


    def send_batch(self,payload):
        # Ensure data is a list of dictionaries
        if not isinstance(payload, list):
            raise ValueError("Data must be a list of dictionaries")
        
        
        _, status_code = self.__controller.send_request(
            endpoint = "process_data",
            method="POST",
            data = payload
        )
        if status_code == 200:
            return True
        else:
            return False
       
# ----------------------------------------------------------------------------------------------
# Setup objects

change_log = Change_log()
hashtable = HashTable(change_log)
queue_manager = BatchQueue()
db_manager = DatabaseManager('C:\\Users\\ksang\\AppData\\Local\\Aronium\\Data\\pos.db')
api_client = ApiClient('http://192.168.0.17:5000')


sync_manager = SyncManager(api_client,hashtable,change_log,queue_manager,db_manager,periodic_timer=3600,sync_now_timer=60)

# start process
sync_manager.start()



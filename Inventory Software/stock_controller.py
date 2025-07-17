from views.stock_view import *


# Controller for all stock related operations
# Format data ready to send to set endpoints and show frames related to stock operations
class StockController:
    def __init__(self, api_controller,app_controller):
        self.__api_controller = api_controller
        self.app_controller = app_controller
        # All frames governed by controller
        self.frames = {
            "Product Search": SearchStock,
            "Product Overview": ProductOverview,
            "Add From List": AddFromList,
            "Rule Groups": RuleGroups,
            "Orders": Orders,
            "RuleGroup Overview":RuleOverview,
            "Add Rule Group": AddRuleGroup,
            "Edit Rule Group": EditRuleGroup,
            "Dashboard":DashboardFrame
        }
    
    # Get frame requesting with the frame name
    def get_frame(self, frame_name, parent,*args):
        if frame_name in self.frames:
            # Pass arguments if any
            if args:
                return self.frames[frame_name](parent,self,args)
            else:
                return self.frames[frame_name](parent, self)
        else:
            raise ValueError(f"Frame {frame_name} does not exist")




    def get_stock_search(self, query):
        # Send to /stock endpoint with search query
        response,status_code = self.__api_controller.send_request(
            endpoint="stock",
            method='GET',
            data= {"query":query}
        )
        return response,status_code

   
    def get_product_info(self, product_id):
        # send to /product_overview with product_id you want to retrieve data on
        response,status_code = self.__api_controller.send_request(
            endpoint="product_overview",
            method='GET',
            data=product_id[0][0]
        )
        if status_code == 200:
            return response
        else:
            return None

    def update_stock_count(self, new_values):
        # send new values to endpoint /stock
        response,status_code = self.__api_controller.send_request(
            endpoint="stock",
            method='PUT',
            data={'updated products': new_values}
        )
        if status_code == 200:
            return True
        else:
            return False

    def get_rule_search(self, query=""):
        # Get all rule associated with query or all rules if query is emmpty
        response,status_code = self.__api_controller.send_request(
            endpoint="rulegroups",
            method='GET',
            data={"query":query}
        )
        if status_code == 200:
            return response
        else:
            return None

        
    def get_rule_info(self,rule_id):
        # Get rule information on rule_id specified
        response,status_code = self.__api_controller.send_request(
            endpoint="rule_overview",
            method="GET",
            data={"rule_id":rule_id}
        )
        if status_code == 200:
            return response
        else:
            return None



    def create_rulegroup(self,category,rule_name,min_stock,product_ids=None):
        # Send rule to be created 
        response,status_code = self.__api_controller.send_request(
        endpoint="rulegroups",
        method='POST',
        data={"Category":category,"Name":rule_name,"Minimum Stock":min_stock,"Product IDs":product_ids}
        )
        if status_code == 200:
            return True,""
        else:
            # Rule was not valid. return the response with it to show to user
            return False,response
       


    def update_rulegroup(self,new_rule):
        response,status_code = self.__api_controller.send_request(
        endpoint="rulegroups",
        method="PUT",
        data=new_rule
        )
        if status_code == 200:
            return True,""
        else:
            return False,response



    def delete_rulegroup(self,rule_id):
        response,status_code = self.__api_controller.send_request(
        endpoint="rulegroups",
        method='DELETE',
        data=rule_id
        )
        



    def get_order_list(self, query):
        response,status_code = self.__api_controller.send_request(
            endpoint="orders",
            method='GET',
            data={'query': query} 
        )
        if status_code == 200:
            return response
        else:
            return None

        

    def get_categories(self):
        response,status_code = self.__api_controller.send_request(
            endpoint="categories",
            method='GET'
        )
        if status_code == 200:
            return response
        else:
            return []


    def get_dashboard_data(self):
        """Retrieve data for the dashboard, including sales and revenue."""
        response,status_code = self.__api_controller.send_request(
            endpoint="dashboard",
            method='GET'
        )
        if status_code == 200:
            return response
        else:
            return None

    def return_stock_alerts(self):
        response,status_code = self.__api_controller.send_request(
            endpoint="stock_alerts",
            method='GET'
        )
        if status_code == 200: 
            return response
        else:
            return None
        

    def clear_stock_alerts(self):
        # Dont require output so ignore
        _ = self.__api_controller.send_request(
            endpoint="stock_alerts",
            method='POST',
            data = "Clear Stock"
            
        )
    


    def sync_request(self,data):
        response,status_code = self.__api_controller.send_request(
            endpoint="sync_now",
            method="POST",
            data = data
        )
        return response,status_code
    


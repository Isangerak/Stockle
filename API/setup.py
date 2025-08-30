import sqlite3
from HashAlgorithm import SHA1
import json



def create_db(path):
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # SQL statements to create the tables
    create_tables_sql = """
    -- Create RuleGroup Table
    CREATE TABLE IF NOT EXISTS RuleGroup (
        rule_group_id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_name TEXT NOT NULL UNIQUE,
        category TEXT,
        min_stock INTEGER NOT NULL
    );

    -- Create Product Table
    CREATE TABLE IF NOT EXISTS Product (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        barcode TEXT NOT NULL,
        name TEXT,
        category TEXT,
        price_sell REAL NOT NULL,
        vat REAL,
        quantity INTEGER DEFAULT 0,
        category_rule_group_id INTEGER,
        independent_rule_group_id INTEGER,
        FOREIGN KEY (category_rule_group_id) REFERENCES RuleGroup(rule_group_id) ON DELETE SET NULL,
        FOREIGN KEY (independent_rule_group_id ) REFERENCES RuleGroup(rule_group_id) ON DELETE SET NULL
    );

 

    -- Create Order Table
    CREATE TABLE IF NOT EXISTS `Order` (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE
    );

    -- Create Sold Table
    CREATE TABLE IF NOT EXISTS 'Sold' (
        sold_id INTEGER PRIMARY KEY AUTOINCREMENT,
        barcode TEXT,
        amount_sold INTEGER,
        date DATETIME
        );


    -- Create Stock Alert Table
    CREATE TABLE IF NOT EXISTS 'stock_alerts' (
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        barcode TEXT,
        message TEXT,
        FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE
        );

 
    """

    cursor.executescript(create_tables_sql)
    conn.commit()
    cursor.execute("SELECT * FROM Product;")
    
    conn.close()
    print("Database setup complete.")




def create_stock_trigger(path):
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    trigger_sql = """
    -- Trigger to check stock when quantity decreases below min_stock, prioritizing independent_rule_group_id
    CREATE TRIGGER check_min_stock_after_update_independent
    AFTER UPDATE OF quantity ON Product
    FOR EACH ROW
    WHEN NEW.independent_rule_group_id IS NOT NULL
    BEGIN
        INSERT INTO `Order` (product_id)
        SELECT NEW.product_id
        WHERE NEW.quantity <= (SELECT min_stock FROM RuleGroup WHERE rule_group_id = NEW.independent_rule_group_id)
        AND NOT EXISTS (
            SELECT 1 
            FROM `Order` 
            WHERE product_id = NEW.product_id
        );
    END;

    -- Trigger to check stock when quantity decreases below min_stock, fallback to category_rule_group_id
    CREATE TRIGGER check_min_stock_after_update_category
    AFTER UPDATE OF quantity ON Product
    FOR EACH ROW
    WHEN NEW.independent_rule_group_id IS NULL AND NEW.category_rule_group_id IS NOT NULL
    BEGIN
        INSERT INTO `Order` (product_id)
        SELECT NEW.product_id
        WHERE NEW.quantity <= (SELECT min_stock FROM RuleGroup WHERE rule_group_id = NEW.category_rule_group_id)
        AND NOT EXISTS (
            SELECT 1 
            FROM `Order` 
            WHERE product_id = NEW.product_id
        );
    END;

    
    -- Trigger to remove order when quantity increases above min_stock for independent_rule_group_id
    CREATE TRIGGER remove_order_if_above_min_stock_independent
    AFTER UPDATE OF quantity ON Product
    FOR EACH ROW
    WHEN NEW.independent_rule_group_id IS NOT NULL
    BEGIN
        DELETE FROM `Order`
        WHERE product_id = NEW.product_id
        AND NEW.quantity > (SELECT min_stock FROM RuleGroup WHERE rule_group_id = NEW.independent_rule_group_id);
    END;
    -- Trigger to remove order when quantity increases above min_stock, fallback to category_rule_group_id
    CREATE TRIGGER remove_order_if_above_min_stock_category
    AFTER UPDATE OF quantity ON Product
    FOR EACH ROW
    WHEN NEW.independent_rule_group_id IS NULL AND NEW.category_rule_group_id IS NOT NULL
    BEGIN
        DELETE FROM `Order`
        WHERE product_id = NEW.product_id
        AND NEW.quantity > (SELECT min_stock FROM RuleGroup WHERE rule_group_id = NEW.category_rule_group_id);
    END;

    

 
    -- Trigger to update product quantity from a sale made
    CREATE TRIGGER update_product_quantity
    AFTER INSERT ON Sold
    FOR EACH ROW
    BEGIN
    -- Subtract the sold amount first
    UPDATE Product
    SET quantity = quantity - NEW.amount_sold
    WHERE barcode = NEW.barcode;

    -- Add to stock alerts ONLY if quantity dropped below 0
    INSERT INTO stock_alerts (message, barcode)
    SELECT 'inaccurate stock levels!', NEW.barcode
    WHERE (SELECT quantity FROM Product WHERE barcode = NEW.barcode) < 0;

    -- Cap quantity at 0 after checking for negative values
    UPDATE Product
    SET quantity = 0
    WHERE barcode = NEW.barcode AND quantity < 0;
    END;

    
    -- Trigger to remove orders for products with no rule groups
    CREATE TRIGGER remove_order_if_no_rule_group
    AFTER UPDATE OF quantity ON Product
    FOR EACH ROW
    WHEN NEW.independent_rule_group_id IS NULL AND NEW.category_rule_group_id IS NULL
    BEGIN
        DELETE FROM `Order`
        WHERE product_id = NEW.product_id;
    END;
    """
    # Execute the SQL script to create the triggers
    cursor.executescript(trigger_sql)
    conn.commit()
    conn.close()

    print("Stock Trigger Created!")




    
def initial_account(path):
    # Admin User Format
    sha = SHA1()
    password_hash = sha.hash("admin",True)
    users_data = [
        {
            "username": "admin",
            "password_hash": password_hash,
            "description": "ROOT USER",
            "permissions": "RWX"
        }
    ]


    # Write user data to JSON file
    with open(path, "w") as file:
        json.dump(users_data, file, indent=4)

    print("Admin Account Created!")


def create_database(path):
    create_db(path)
    create_stock_trigger(path)


def create_account(path):
    initial_account(path)

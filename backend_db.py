import psycopg2
import json
import psycopg2.extras
from datetime import datetime
import base64
from psycopg2.extensions import Binary
from decimal import Decimal
from psycopg2.extras import RealDictCursor

def connection():
    conn = psycopg2.connect(
            database="gadgetrental_db", user='gadgetrental_user', password='12345678', host='127.0.0.1', port= '5432'
    )
    print("connection successfull")
    return conn



def user_signup(request_data):
    conn = connection()
    if conn is None:
        return "Database connection failed", 500
    
    cursor = conn.cursor()
    
    try:
        user_type = request_data.get('userType')
        print(user_type, "it is user_type")
        
        if user_type.lower() == "buyer":
            QUERY1 = '''SELECT MAX(user_id) FROM gizmozone.user_registration;'''
            cursor.execute(QUERY1)
            reg_records = cursor.fetchone()
            no_of_users = reg_records[0] if reg_records and reg_records[0] is not None else 0
            users_no = str(no_of_users + 1).zfill(3)  # Format user ID with leading zeros
            
            print("Generated User ID:", users_no)
            INSERT_QUERY = '''
                INSERT INTO gizmozone.user_registration (
                user_id, first_name, last_name, email, phone_no, password, address, city) 
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(INSERT_QUERY, (
                users_no,
                request_data['first_name'],
                request_data['last_name'],
                request_data['email'],
                request_data['mobile_no'],
                request_data['password'],
                request_data['address'],
                request_data['city']
            ))
            
            QUERY3 = '''SELECT MAX(login_id) FROM gizmozone.user_login;'''
            cursor.execute(QUERY3)
            records = cursor.fetchone()
            next_login_id = (records[0] + 1) if records and records[0] is not None else 1
            
            print("Next Login ID:", next_login_id)
            INSERT_QUERY1 = '''
                INSERT INTO gizmozone.user_login(
                login_id, user_id, email, password) 
                VALUES(%s, %s, %s, %s)
            '''
            cursor.execute(INSERT_QUERY1, (
               next_login_id,
               users_no,
               request_data['email'],
               request_data['password'],
             ))
            conn.commit()

        elif user_type.lower() == "seller":
            QUERY5 = '''SELECT MAX(seller_id) FROM gizmozone.seller;'''
            cursor.execute(QUERY5)
            reg_records = cursor.fetchone()
            no_of_users = reg_records[0] if reg_records and reg_records[0] is not None else 0
            users_no = str(no_of_users + 1).zfill(3)
            
            INSERT_QUERY = '''
                INSERT INTO gizmozone.seller (
                seller_id, first_name, last_name, email, phone_no, password, address, city) 
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
            '''
            cursor.execute(INSERT_QUERY, (
                users_no,
                request_data['first_name'],
                request_data['last_name'],
                request_data['email'],
                request_data['mobile_no'],
                request_data['password'],
                request_data['address'],
                request_data['city']
            ))
            
            QUERY4 = '''SELECT MAX(login_id) FROM gizmozone.seller_login;'''
            cursor.execute(QUERY4)
            records = cursor.fetchone()
            next_login_id = (records[0] + 1) if records and records[0] is not None else 1
            
            print("Next Login ID:", next_login_id)
            INSERT_QUERY1 = '''
                INSERT INTO gizmozone.seller_login(
                login_id, seller_id, email, password) 
                VALUES(%s, %s, %s, %s)
            '''
            cursor.execute(INSERT_QUERY1, (
                next_login_id,
                users_no,
                request_data['email'],
                request_data['password'],
            ))
            conn.commit()
        else:
            return "Invalid user type", 400
        
    except Exception as e:
        print("Error:", str(e))
        conn.rollback()
        return "Error occurred", 500
    finally:
        cursor.close()
        conn.close()

    return "Success"

# def validate_login_details(login_data):
#     print(login_data)
#     conn = connection()
#     cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
#     valid_user = False
#     user_id = None
#     user_type = None  # Distinguish between buyer and seller
#     email_user = login_data['user_email'].strip()
#     password_user = login_data['password'].strip()
#     try:
#         # Check in user_login (buyers)
#         QUERY_BUYER = ''' 
#             SELECT user_id, email, password FROM gizmozone.user_login
#             WHERE email ILIKE %s 
#         '''
#         cursor.execute(QUERY_BUYER, (email_user,))
#         buyer_record = cursor.fetchone()
#         if buyer_record:
#             if buyer_record['password'] == password_user:
#                 valid_user = True
#                 user_id = buyer_record['user_id']
#         # If not found in buyers, check in seller_login
#         if not valid_user:
#             QUERY_SELLER = ''' 
#                 SELECT seller_id, email, password FROM gizmozone.seller_login
#                 WHERE email ILIKE %s 
#             '''
#             cursor.execute(QUERY_SELLER, (email_user,))
#             seller_record = cursor.fetchone()

#             if seller_record:
#                 if seller_record['password'] == password_user:
#                     valid_user = True
#                     user_id = seller_record['seller_id']  # Seller has seller_i
#     except Exception as e:
#         print("Error:", str(e))
#     finally:
#         if conn:
#             cursor.close()
#             conn.close()
#     return valid_user, user_id

def validate_login_details(login_data):
    print(login_data)
    conn = connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    valid_user = False
    user_id = None

    email_user = login_data['user_email'].strip()
    password_user = login_data['password'].strip()
    user_type = login_data['userType'].strip().lower()  # Get user type

    try:
        if user_type == "buyer":
            # Check only in buyer table
            QUERY_BUYER = ''' 
                SELECT user_id, email, password FROM gizmozone.user_login
                WHERE email ILIKE %s 
            '''
            cursor.execute(QUERY_BUYER, (email_user,))
            user_record = cursor.fetchone()

            if user_record and user_record['password'] == password_user:
                valid_user = True
                user_id = user_record['user_id']

        elif user_type == "seller":
            # Check only in seller table
            QUERY_SELLER = ''' 
                SELECT seller_id, email, password FROM gizmozone.seller_login
                WHERE email ILIKE %s 
            '''
            cursor.execute(QUERY_SELLER, (email_user,))
            user_record = cursor.fetchone()

            if user_record and user_record['password'] == password_user:
                valid_user = True
                user_id = user_record['seller_id']

    except Exception as e:
        print("Error:", str(e))

    finally:
        if conn:
            cursor.close()
            conn.close()

    return valid_user, user_id  # user_id corresponds to buyer or seller based on user_type




def rent_item(request_data):
    conn = connection()
    cursor = conn.cursor()
    try:
    
        # Query to get the max id (this part stays the same)
        QUERY1 = '''
            SELECT MAX(id) FROM gizmozone.rentitems;
        '''
        cursor.execute(QUERY1)
        records = cursor.fetchall()
        next_id = records[0][0] + 1 if records and records[0][0] is not None else 1

        # Decode the Base64 image string into bytes
        image_data = base64.b64decode(request_data['image'])

        # Parameterized insert query
        INSERT_QUERY = '''
            INSERT INTO gizmozone.RentItems(
                id,
                user_id,
                product_name,
                key_feature,
                description,
                category,
                brand,
                model,
                rental_price_per_day,
                availability_status,
                images,
                location
            ) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''

        # Executing the query with parameters (pass the image data as bytes)
        cursor.execute(INSERT_QUERY, (
            next_id,
            request_data['user_id'],
            request_data['product_name'],
            request_data['key_feature'],
            request_data['description'],
            request_data['category'],
            request_data['brand'],
            request_data['model'],
            request_data['rental_price_per_day'],
            request_data['availability_status'],
            psycopg2.Binary(image_data),  # Use psycopg2.Binary to pass the image as bytes
            request_data['location']
        ))

        # Commit the transaction
        conn.commit()

    except Exception as e:
        print("Error occurred:", str(e))
        conn.rollback()  # Rollback in case of an error
    finally:
        if conn:
            cursor.close()
            conn.close()
    return "Success"

def validate_base64(base64_string):
    try:
        base64.b64decode(base64_string, validate=True)
        return True
    except Exception as e:
        print(f"Invalid Base64 string: {e}")
        return False

def fetch_items_from_db():
    try:
        # Connect to the database
        conn = connection()
        cursor = conn.cursor()

        # Query to fetch all data from the table
        cursor.execute("""
            SELECT filename, image_data, user_id, product_name, key_feature, description,
                   category, brand, model, rental_price_per_day, availability_status, location, item_id
            FROM gizmozone.images
        """)
        items = cursor.fetchall()

        # if not items:
        #     raise HTTPException(status_code=404, detail="No items found")

        # Prepare a list of item details, encoding image_data to Base64
        item_list = [
            {
                "filename": item[0],
                "image_data": base64.b64encode(item[1]).decode("utf-8"),  # Encode image data to Base64
                "user_id": item[2],
                "product_name": item[3],
                "key_feature": item[4],
                "description": item[5],
                "category": item[6],
                "brand": item[7],
                "model": item[8],
                "rental_price_per_day": item[9],
                "availability_status": item[10],
                "location": item[11],
                "item_id": item[12]
            }
            for item in items
        ]
        cursor.close()
        conn.close()
        return item_list
    except Exception as e:
        print("error occured", e)
    finally:
        if conn:
            cursor.close()
            conn.close()


def update_item_in_db(item_id: int, item) -> bool:
    try:
        # Connect to the database
        with connection() as conn:
            with conn.cursor() as cursor:
                # Execute the update query
                cursor.execute("""
                    UPDATE gizmozone.images
                    SET product_name = %s, key_feature = %s, description = %s, category = %s, 
                        brand = %s, model = %s, rental_price_per_day = %s, availability_status = %s, location = %s
                    WHERE item_id = %s
                """, (
                    item.product_name,
                    item.key_feature,
                    item.description,
                    item.category,
                    item.brand,
                    item.model,
                    item.rental_price_per_day,
                    item.availability_status,
                    item.location,
                    item_id
                ))

                print(item_id,item)

                # Commit the transaction
                conn.commit()

                # Check if the update was successful
                return cursor.rowcount > 0
    except Exception as e:
        # Log or handle the error appropriately
        print(f"Database error: {e}")
        raise

def add_to_cart(user_id: int, item_id: int, quantity: int) -> str:
    try:
        conn = connection()
        cursor = conn.cursor()
        
        # Check if the item already exists in the cart
        cursor.execute("""
            SELECT * 
            FROM gizmozone.cart
            WHERE user_id = %s AND item_id = %s
        """, (user_id, item_id))
        
        existing_item = cursor.fetchone()
        
        if existing_item:
            # Update the quantity if the item already exists
            cursor.execute("""
                UPDATE gizmozone.cart
                SET quantity = quantity + %s
                WHERE user_id = %s AND item_id = %s
            """, (quantity, user_id, item_id))
            message = "Item quantity updated in the cart."
        else:
            # Insert the item into the cart if it doesn't exist
            cursor.execute("""
                INSERT INTO gizmozone.cart (user_id, item_id, quantity)
                VALUES (%s, %s, %s)
            """, (user_id, item_id, quantity))
            message = "Item added to the cart."
        
        # Commit the transaction
        conn.commit()
        
        return message
    except Exception as e:
        # Rollback in case of an error
        if connection:
            conn.rollback()
        print(f"Database error: {e}")
        return "An error occurred while adding to the cart."
    finally:
        if conn:
            cursor.close()
            conn.close()

def support_details(request_data):
    conn = connection()
    cursor = conn.cursor()
    try:
    
        # Query to get the max id (this part stays the same)
        QUERY1 = '''
            SELECT MAX(id) FROM gizmozone.support;
        '''
        cursor.execute(QUERY1)
        records = cursor.fetchall()
        next_id = records[0][0] + 1 if records and records[0][0] is not None else 1

        # Decode the Base64 image string into bytes
       

        # Parameterized insert query
        INSERT_QUERY = '''
            INSERT INTO gizmozone.support(
                id,
               name,
               email,
               message
            ) 
            VALUES('{}','{}','{}','{}')'''.format(
                        next_id,
                        request_data['name'],
                        request_data['email'],
                        request_data['message'],
                    )

        cursor.execute(INSERT_QUERY)
        conn.commit()

    except Exception as e:
        print("Error occurred:", str(e))
        conn.rollback()  # Rollback in case of an error
    finally:
        if conn:
            cursor.close()
            conn.close()
    return "Success"


def get_item_from_db(item_id: int):
    try:
        conn = connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT 
                c.item_id, 
                i.product_name, 
                i.key_feature, 
                i.rental_price_per_day, 
                ENCODE(i.image_data, 'base64') AS image_data, 
                c.quantity
            FROM gizmozone.cart c
            JOIN gizmozone.images i ON c.item_id = i.item_id
            WHERE c.item_id = %s 
        """
        cursor.execute(query, (item_id,))
        item = cursor.fetchone()

        cursor.close()
        conn.close()

        return decimal_to_float(item) if item else None

    except Exception as e:
        print("Error occurred:", str(e))
        conn.rollback()  # Rollback in case of an error
    finally:
        if conn:
            cursor.close()
            conn.close()

# Convert decimal values to float (if needed)
def decimal_to_float(data):
    if isinstance(data, dict):
        return {k: float(v) if isinstance(v, (int, float)) else v for k, v in data.items()}
    return data

def get_user_profile(user_id):
    try:
        conn = connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # First, search in user_registration table
        query_user = """
            SELECT 
                user_id, 
                first_name, 
                last_name,
                email, 
                phone_no, 
                address, 
                city
            FROM gizmozone.user_registration
            WHERE email = %s
        """
        cursor.execute(query_user, (user_id,))
        user_profile = cursor.fetchone()

        # If not found in user_registration, check the seller table
        if not user_profile:
            query_seller = """
                SELECT 
                    seller_id AS user_id, 
                    first_name, 
                    last_name,
                    email, 
                    phone_no, 
                    address, 
                    city
                FROM gizmozone.seller
                WHERE email = %s
            """
            cursor.execute(query_seller, (user_id,))
            user_profile = cursor.fetchone()

        cursor.close()
        conn.close()
        return user_profile if user_profile else None

    except Exception as e:
        print("Error occurred:", str(e))
        conn.rollback()  # Rollback in case of an error
    finally:
        if conn:
            cursor.close()
            conn.close()

def convert_decimal(obj):
    """ Convert Decimal to float for JSON serialization """
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("Type not serializable")


def get_profile_data(item):
    conn = connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    print("Category:", item)
    
    json_result = []  # Ensure json_result is always initialized
    
    try:
        QUERY = '''
            SELECT image_data, user_id, product_name, key_feature, description,
                   category, brand, model, rental_price_per_day, availability_status, location, item_id
            FROM gizmozone.images
            WHERE category = %s
        '''
        
        cursor.execute(QUERY, (item,))  # Use parameterized query
        records = cursor.fetchall()

        # Convert memoryview (binary image data) to base64
        for record in records:
            if record["image_data"]:  # If image data exists
                record["image_data"] = base64.b64encode(record["image_data"]).decode("utf-8")
        
        json_result = json.dumps(records,default=convert_decimal)  # Convert to JSON
        
        print(json_result)
    
    except Exception as e:
        print("Error:", str(e), "Occurred")
    
    finally:
        if conn:
            cursor.close()
            conn.close()
    
    return json_result

def update_user_in_db(user):
    conn = connection()
    cursor = conn.cursor()
    try:
        # Check if the user exists in user_registration
        cursor.execute("SELECT user_id FROM gizmozone.user_registration WHERE email = %s", (user.email,))
        user_profile = cursor.fetchone()
        if user_profile:
            query = """
                UPDATE gizmozone.user_registration
                SET first_name = %s, last_name = %s, email = %s, phone_no = %s, address = %s, city = %s
                WHERE email = %s
            """
            cursor.execute(query, (user.first_name, user.last_name, user.email, user.phone_no, user.address, user.city, user.email))
            conn.commit()
            return {"message": "User updated successfully", "role": "user"}
        # Check if the user exists in seller table
        cursor.execute("SELECT seller_id FROM gizmozone.seller WHERE email = %s", (user.email,))
        seller_profile = cursor.fetchone()
        if seller_profile:
            query = """
                UPDATE gizmozone.seller
                SET first_name = %s, last_name = %s, email = %s, phone_no = %s, address = %s, city = %s
                WHERE email = %s
            """
            cursor.execute(query, (user.first_name, user.last_name, user.email, user.phone_no, user.address, user.city, user.email))
            conn.commit()
            return {"message": "Seller updated successfully", "role": "seller"}
        return None  # User not found in both tables
    except Exception as e:
        raise Exception(str(e))
    finally:
        cursor.close()
        conn.close()

def get_user_from_db(user_email):
    """Fetch user details based on email from user_registration or seller table."""
    conn = connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        # Check in user_registration table first
        query = "SELECT user_id, first_name, last_name, email, phone_no, address, city FROM gizmozone.user_registration WHERE email = %s"
        cursor.execute(query, (user_email,))
        user_profile = cursor.fetchone()
        if user_profile:
            return {"profile": user_profile, "role": "user"}
        # Check in seller table if not found in user_registration
        query = "SELECT seller_id AS user_id, first_name, last_name, email, phone_no, address, city FROM gizmozone.seller WHERE email = %s"
        cursor.execute(query, (user_email,))
        seller_profile = cursor.fetchone()
        if seller_profile:
            return {"profile": seller_profile, "role": "seller"}
        return None  # User not found in both tables
    except Exception as e:
        raise Exception(str(e))
    finally:
        cursor.close()
        conn.close()

def remove_cart_item_from_db(item_id: int, user_id: int):
    """Removes an item from the cart based on item_id and user_id."""
    conn = connection()
    cursor = conn.cursor()
    try:
        query = """
            DELETE FROM gizmozone.cart 
            WHERE item_id = %s AND user_id = %s
        """
        cursor.execute(query, (item_id, user_id))
        conn.commit()
        return {"message": "Item removed successfully."}
    except Exception as e:
        print(f"Error removing cart item: {e}")
    finally:
        cursor.close()
        conn.close()

def get_cart_items_from_db(user_id: int):
    try:
        with connection() as conn:
            with conn.cursor() as cursor:
                # Fetch cart details with item information for the given user_id
                query = """
                    SELECT 
                        c.item_id, 
                        i.product_name, 
                        i.key_feature, 
                        i.rental_price_per_day, 
                        ENCODE(i.image_data, 'base64') AS image_data, 
                        c.quantity
                    FROM gizmozone.cart c
                    JOIN gizmozone.images i ON c.item_id = i.item_id
                    WHERE c.user_id = %s
                """
                cursor.execute(query, (user_id,))
                rows = cursor.fetchall()
                if not rows:
                    return None  # Handle not found case in the route
                return [
                    {
                        "item_id": row[0],
                        "product_name": row[1],
                        "key_feature": row[2],
                        "rental_price_per_day": float(row[3]),
                        "image_data": row[4],
                        "quantity": row[5],
                    }
                    for row in rows
                ]
    except Exception as e:
        print(f"Database error: {e}")

def get_wishlist_items_from_db(user_id: int):
    try:
        with connection() as conn:
            with conn.cursor() as cursor:
                # Fetch cart details with item information for the given user_id
                query = """
                    
                 SELECT 
                 w.item_id, 
                 i.product_name, 
                 i.key_feature, 
                 i.rental_price_per_day, 
                 ENCODE(i.image_data, 'base64') AS image_data
                 FROM gizmozone.wishlist w
                 JOIN gizmozone.images i ON w.item_id = i.item_id
                 WHERE w.user_id = %s
                """
                cursor.execute(query, (user_id,))
                rows = cursor.fetchall()
                if not rows:
                    return None  # Handle not found case in the route
                return [
                    {
                        "item_id": row[0],
                        "product_name": row[1],
                        "key_feature": row[2],
                        "rental_price_per_day": float(row[3]),
                        "image_data": row[4]

                    }
                    for row in rows
                ]
    except Exception as e:
        print(f"Database error: {e}")

        
def insert_rental_item(item_data, filename, image_data):
    conn = None
    cursor = None
    try:
        conn = connection()
        cursor = conn.cursor()

        # Extract values from dictionary
        insert_query = """
            INSERT INTO gizmozone.images (
                filename, image_data, user_id, product_name, key_feature, description, category, brand, model,
                rental_price_per_day, availability_status, location
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING item_id;
        """

        cursor.execute(
            insert_query,
            (
                filename, image_data, item_data["user_id"], item_data["product_name"], item_data["key_feature"],
                item_data["description"], item_data["category"], item_data["brand"], item_data["model"],
                item_data["rental_price_per_day"], item_data["availability_status"], item_data["location"]
            )
        )
        
        item_id = cursor.fetchone()[0]
        conn.commit()
        return item_id

    except Exception as e:
        if conn:
            conn.rollback()
        raise e

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

import base64

def get_user_items_from_db(user_id: int):
    try:
        with connection() as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT image_data, user_id, product_name, key_feature, description,
                           category, brand, model, rental_price_per_day, availability_status, location, item_id
                    FROM gizmozone.images
                    WHERE user_id = %s
                """
                cursor.execute(query, (user_id,))
                rows = cursor.fetchall()

                if not rows:
                    return []  # Return an empty list instead of None

                # Get column names dynamically
                columns = [desc[0] for desc in cursor.description]

                items = []
                for row in rows:
                    item = dict(zip(columns, row))  # Convert row to dict
                    # Convert image_data to Base64 if present
                    if item["image_data"]:
                        item["image_data"] = base64.b64encode(item["image_data"]).decode("utf-8")
                    # Convert rental_price_per_day to float
                    if "rental_price_per_day" in item and item["rental_price_per_day"] is not None:
                        item["rental_price_per_day"] = float(item["rental_price_per_day"])
                    items.append(item)

                return items
    except Exception as e:
        if conn:
            conn.rollback()
        raise e

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def add_to_wishlist(user_id: int, item_id: int) -> str:
    try:
        conn = connection()
        cursor = conn.cursor()
        
        # Check if the item already exists in the wishlist
        cursor.execute("""
            SELECT * 
            FROM gizmozone.wishlist
            WHERE user_id = %s AND item_id = %s
        """, (user_id, item_id,))
        
        existing_item = cursor.fetchone()
        
        if existing_item:
            # If the item already exists, just return a message (no need to update)
            message = "Item already exists in the wishlist."
        else:
            # Insert the item into the wishlist if it doesn't exist
            cursor.execute("""
                INSERT INTO gizmozone.wishlist (user_id, item_id)
                VALUES (%s, %s)
            """, (user_id, item_id,))
            message = "Item added to the wishlist."
        
        # Commit the transaction
        conn.commit()
        
        return message
    except Exception as e:
        # Rollback in case of an error
        if conn:
            conn.rollback()
        print(f"Database error: {e}")
        return "An error occurred while adding to the wishlist."
    finally:
        if conn:
            cursor.close()
            conn.close()

def remove_wishlist_item_from_db(item_id: int, user_id: int):
    """Removes an item from the cart based on item_id and user_id."""
    conn = connection()
    cursor = conn.cursor()
    try:
        query = """
            DELETE FROM gizmozone.wishlist 
            WHERE item_id = %s AND user_id = %s
        """
        cursor.execute(query, (item_id, user_id))
        conn.commit()
        return {"message": "Item removed successfully."}
    except Exception as e:
        print(f"Error removing cart item: {e}")
    finally:
        cursor.close()
        conn.close()
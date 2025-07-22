from fastapi import FastAPI,HTTPException,Response,Request,UploadFile, File, Form,Query
import backend_db as fsd_db
from typing import Dict
from fastapi.responses import JSONResponse,StreamingResponse
import schemas
import base64
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor
from io import BytesIO
from psycopg2 import sql
from typing import List, Dict
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:6078",  # Frontend origin (Flask)
        "http://localhost:6078",  # Alternative frontend origin
    ],
    allow_credentials=True,  # Allow cookies/credentials if needed
    allow_methods=["*"],     # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],     # Allow all headers
)

def connection():
    conn = psycopg2.connect(
            database="gadgetrental_db", user='gadgetrental_user', password='12345678', host='127.0.0.1', port= '5432'
    )
    print("connection successfull")
    return conn

# async def connection():
#     return await asyncpg.connect(
#         database="gadgetrental_db", user='gadgetrental_user', password='12345678', host='127.0.0.1', port= '5432'
#     )

@app.get("/")
def read_root():
    return {
        "message": "Hello, FastAPI!",
        "signup_endpoint": "/user_signup",  # This is your POST endpoint
        "note": "This endpoint accepts POST requests with user signup details in JSON format."
    }

@app.post("/user_signup")
def user_signup(signup_details:schemas.UserSignUp):
    print(signup_details)
    result = fsd_db.user_signup(signup_details.dict())
    response = {
        "data" : result
    }
    return JSONResponse(content=response)

@app.post("/attempt_to_login_for_user")
def attempt_to_login_for_user(login_data:schemas.LoginForUser):
    valid_user_login = ""
    valid_user, user_id = fsd_db.validate_login_details(login_data.dict())
    if(valid_user):
        valid_user_login = "Login Successful"
    else:
        valid_user_login = "Login Failed"

    response = {
        "status" : valid_user_login,
        "user_id": user_id
    }
    return JSONResponse(content=response, status_code=200)

@app.get("/display_cart")
def display_cart():
    result = fsd_db.get_display_cart_data()
    return {"data": result}
    
@app.post("/rent_item/")
async def rent_item(
    product_name: str = Form(...),
    key_feature: str = Form(None),
    description: str = Form(...),
    category: str = Form(...),
    brand: str = Form(...),
    model: str = Form(...),
    rental_price_per_day: float = Form(...),
    availability_status: bool = Form(...),
    location: str = Form(...),
    user_id: int = Form(...),
    image: UploadFile = File(...)
):
    try:
        # Read image data
        image_data = await image.read()
        filename = image.filename

        # Connect to the database
        conn = connection()
        cursor = conn.cursor()

        # Insert data into the database
        insert_query = """
            INSERT INTO gizmozone.images (
                filename,image_data, user_id, product_name, key_feature, description, category, brand, model,
                rental_price_per_day, availability_status, location
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING item_id;
        """
        cursor.execute(
            insert_query,
            (filename,image_data,  user_id, product_name, key_feature, description, category, brand, model,
             rental_price_per_day, availability_status, location)
        )
        item_id = cursor.fetchone()[0]
        print(item_id, "item id will be this")

        # Commit and close the connection
        conn.commit()
        cursor.close()
        conn.close()

        return {"id": item_id, "message": "Item rented successfully!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error renting item: {str(e)}")


@app.get("/get_items/")
async def get_items():
    items = fsd_db.fetch_items_from_db()  # Fetch the items from the database
    return {"items": items}

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    try:
        # Connect to the database
        conn = connection()
        cursor = conn.cursor()

        # Query to fetch a single item by its ID
        cursor.execute("""
            SELECT filename, image_data, user_id, product_name, key_feature, description,
                   category, brand, model, rental_price_per_day, availability_status, location, item_id
            FROM gizmozone.images
            WHERE item_id = %s
        """, (item_id,))
        item = cursor.fetchone()

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Prepare the item details, encoding image_data to Base64
        item_details = {
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

        cursor.close()
        conn.close()

        return item_details

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/update/{item_id}")
async def update_item(item_id: int, item: schemas.UpdateItems):
    try:
        # Call the backend function to perform the update
        result = fsd_db.update_item_in_db(item_id, item)
        print(result)
        if not result:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"message": "Item updated successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating item: {str(e)}")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    try:
        # Connect to the database
        conn = connection()
        cursor = conn.cursor()

        # Delete from the cart table first (to prevent foreign key issues)
        cursor.execute("DELETE FROM gizmozone.cart WHERE item_id = %s", (item_id,))

        # Delete from the images table
        cursor.execute("DELETE FROM gizmozone.images WHERE item_id = %s", (item_id,))

        # Commit the changes
        conn.commit()

        # Check if any row was deleted
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found")

        # Close the cursor and connection
        cursor.close()
        conn.close()

        return {"message": "Item deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting the item: {str(e)}")

@app.post("/cart/add")
def add_item_to_cart(cart_item: schemas.CartItem):
    try:
        message = fsd_db.add_to_cart(
            user_id=cart_item.user_id,
            item_id=cart_item.item_id,
            quantity=cart_item.quantity,
        )
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.get("/cart/items")
def get_cart_items(user_id: int):
    cart_items = fsd_db.get_cart_items_from_db(user_id)
    if not cart_items:
        raise HTTPException(status_code=404, detail="No items found in the cart.")
    return JSONResponse(content=cart_items, status_code=200)

@app.delete("/cart/items/{item_id}")
def remove_cart_item(item_id: int, user_id: int):
    try:
        return fsd_db.remove_cart_item_from_db(item_id, user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/wishlist/items")
def get_cart_items(user_id: int = Query(..., description="User ID is required")):
    wishlist_items = fsd_db.get_wishlist_items_from_db(user_id)
    if not wishlist_items:
        raise HTTPException(status_code=404, detail="No items found in the wishlist.")
    return JSONResponse(content=wishlist_items, status_code=200)

def decimal_to_float(item):
    # Convert Decimal fields to float
    if isinstance(item, Decimal):
        return float(item)
    if isinstance(item, dict):
        return {key: decimal_to_float(value) for key, value in item.items()}
    if isinstance(item, list):
        return [decimal_to_float(element) for element in item]
    return item

@app.post('/support')
def support_details(supportDetail:schemas.Support):
    result = fsd_db.support_details(supportDetail.dict())
    response = {
        "data" : result
    }
    return JSONResponse(content=response)

@app.get("/item/{item_id}")
def get_item_details(item_id: int):
        item = fsd_db.get_item_from_db(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found for the given user")
        return JSONResponse(content=item, status_code=200)

@app.get("/user_profile/{user_email}")
def user_profile(user_email):
        item = fsd_db.get_user_profile(user_email)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found for the given user")
        return JSONResponse(content=item, status_code=200)


@app.get("/get_user/{user_email}")
async def get_user(user_email: str):
    try:
        result = fsd_db.get_user_from_db(user_email)
        if result:
            return result
        raise HTTPException(status_code=404, detail="User not found in both tables")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/update_user/{user_email}")
async def update_user(user: schemas.UpdateUser):
    try:
        result = fsd_db.update_user_in_db(user)
        if result:
            return result
        raise HTTPException(status_code=404, detail="User not found in both tables")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/search')
def search(search_details:schemas.Search):
    print(search_details)
    result = fsd_db.get_profile_data(search_details.category)
    response = {
        "data" : result
    }
    return JSONResponse(content=response)

@app.get("/get_user_item/{user_id}")
def get_user_items(user_id: int):
    cart_items = fsd_db.get_user_items_from_db(user_id)
    print(cart_items)
    if not cart_items:
        raise HTTPException(status_code=404, detail="No items found in the cart.")
    return JSONResponse(content=cart_items, status_code=200)

@app.post("/wishlist/add")
def add_item_to_wishlist(wish_item: schemas.WishItem):
    try:
        message = fsd_db.add_to_wishlist(
            user_id=wish_item.user_id,
            item_id=wish_item.item_id,
        )
        print(message)
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
@app.delete("/wishlist/items/{user_id}/{item_id}")
def remove_wishlist_item(item_id: int, user_id: int):
    try:
        return fsd_db.remove_wishlist_item_from_db(item_id, user_id)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/orders/")
async def create_order(order: schemas.OrderRequest):
    conn = None
    cursor = None
    try:
        # Connect to database
        conn = fsd_db.connection()  # Reuse your connection function
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Insert into orders table
        cursor.execute(
            """
            INSERT INTO gizmozone.orders (user_id, total_price, status)
            VALUES (%s, %s, %s)
            RETURNING order_id
            """,
            (order.user_id, order.total_price, "Pending")
        )
        order_id = cursor.fetchone()["order_id"]

        # Insert into order_items table
        for item in order.items:
            cursor.execute(
                """
                INSERT INTO gizmozone.order_items (order_id, item_id, rental_price_per_day, quantity)
                VALUES (%s, %s, %s, %s)
                """,
                (order_id, item.item_id, item.rental_price_per_day, item.quantity)
            )

        # Commit transaction
        conn.commit()

        # Fetch order details for confirmation
        cursor.execute(
            """
            SELECT o.order_id, o.user_id, o.total_price, o.order_date, o.status,
                   oi.item_id, oi.rental_price_per_day, oi.quantity,
                   i.product_name, i.image_data, i.filename
            FROM gizmozone.orders o
            JOIN gizmozone.order_items oi ON o.order_id = oi.order_id
            JOIN gizmozone.images i ON oi.item_id = i.item_id
            WHERE o.order_id = %s
            """,
            (order_id,)
        )
        order_details = cursor.fetchall()

        # Encode image_data to Base64
        for item in order_details:
            if item["image_data"]:
                item["image_data"] = base64.b64encode(item["image_data"]).decode("utf-8")

        return {"order_id": order_id, "details": order_details}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


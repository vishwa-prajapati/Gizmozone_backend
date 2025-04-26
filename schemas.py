from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional

class UserSignUp(BaseModel):
    first_name : str
    last_name : str
    email :str
    mobile_no :int
    password: str
    city:str
    address:str
    userType:str
    
    
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class LoginForUser(BaseModel):
    user_email : str
    password : str
    userType:str
    
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class RentItems(BaseModel):
    user_id: int
    product_name: str
    key_feature: str | None = None
    description: str
    category: str
    brand: str
    model: str
    rental_price_per_day: float
    availability_status: bool
    location: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class RentItemPage(BaseModel):
    user_id: int
    item_id: str

class UpdateItems(BaseModel):
    # user_id:int
    product_name: str
    key_feature: str = None
    description: str
    category: str
    brand: str
    model: str
    rental_price_per_day: int
    availability_status: bool
    location: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class CartItem(BaseModel):
    user_id: int
    item_id: int
    quantity:int

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class Support(BaseModel):
    name:str
    email:str
    message:str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class UpdateUser(BaseModel):
    email:str
    first_name: str
    last_name: str
    phone_no: str
    address: str
    city:str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class Search(BaseModel):
    category: str

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class EmailRequest(BaseModel):
    email: EmailStr


class WishItem(BaseModel):
    user_id:int
    item_id: int

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class OrderItem(BaseModel):
    item_id: int
    rental_price_per_day: float
    quantity: int = 1  # Number of rental days or items

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class OrderRequest(BaseModel):
    user_id: int
    items: list[OrderItem]
    total_price: float

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True

class EmailRequest(BaseModel):
    email: EmailStr


# Request Model for Verifying OTP
class VerifyRequest(BaseModel):
    email: EmailStr
    otp: str
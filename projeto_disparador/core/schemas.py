from ninja import Schema
from pydantic import EmailStr

class RegisterIn(Schema):
    email: EmailStr
    name: str
    password: str

class LoginIn(Schema):
    email: EmailStr
    password: str

class TokenOut(Schema):
    access_token: str
    token_type: str
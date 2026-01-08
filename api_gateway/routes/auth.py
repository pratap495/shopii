from fastapi import APIRouter
from pydantic import BaseModel
import uuid
from rabbitmq.publisher import publish_event

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str

@router.post("/register")
def register(payload: RegisterRequest):
    request_id = str(uuid.uuid4())

    publish_event(
        event_type="USER_REGISTER",
        data={
            "requestId": request_id,
            "username": payload.username,
            "email": payload.email,
            "password": payload.password
        }
    )

    return {
        "requestId": request_id,
        "status": "PROCESSING",
        "message": "Registration request queued"
    }

@router.post("/login")
def login(payload: LoginRequest):
    request_id = str(uuid.uuid4())

    publish_event(
        event_type="USER_LOGIN",
        data={
            "requestId": request_id,
            "username": payload.username,
            "password": payload.password
        }
    )

    return {
        "requestId": request_id,
        "status": "PROCESSING",
        "message": "Login request queued"
    }

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest):
    request_id = str(uuid.uuid4())

    publish_event(
        event_type="FORGOT_PASSWORD",
        data={
            "requestId": request_id,
            "email": payload.email
        }
    )

    return {
        "requestId": request_id,
        "status": "PROCESSING",
        "message": "OTP request queued"
    }

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest):
    request_id = str(uuid.uuid4())

    publish_event(
        event_type="RESET_PASSWORD",
        data={
            "requestId": request_id,
            "email": payload.email,
            "otp": payload.otp,
            "new_password": payload.new_password
        }
    )

    return {
        "requestId": request_id,
        "status": "PROCESSING",
        "message": "Password reset request queued"
    }
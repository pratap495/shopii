from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from routes.products import router as product_router
from routes.auth import router as auth_router
from routes.database import AuthDatabase

app = FastAPI(title="Unified Commerce API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EmailCheck(BaseModel):
    email: str

class LoginRequest(BaseModel):
    email: str
    password: str

db = AuthDatabase()

@app.post("/auth/check-email")
async def check_email(data: EmailCheck):
    exists = db.check_email_exists(data.email)
    return {"exists": exists}

@app.post("/auth/login")
async def login(data: LoginRequest):
    print(f"Login request received for: {data.email}")
    result = db.verify_user(data.email, data.password)
    if result["status"] == "ERROR":
        raise HTTPException(status_code=401, detail=result["message"])
    return result

# Include routers after defining custom overrides to ensure precedence
app.include_router(product_router, prefix="/products")
app.include_router(auth_router, prefix="/auth")

@app.get("/")
def health():
    return {"status": "API Gateway running"}

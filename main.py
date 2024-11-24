import uvicorn
import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from supabase import create_client, Client
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse


load_dotenv()
app = FastAPI()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/auth/login/{provider}")
async def login(provider: str):
    # Generate the login URL for Google or GitHub
    url = f"{supabase_url}/auth/v1/authorize?provider={provider}&redirect_to=https://smartgreen-kappa.vercel.app/auth/callback"
    return RedirectResponse(url)

@app.get("/auth/callback", response_class=HTMLResponse)
async def callback():
    with open("callback.html") as f:
        return HTMLResponse(content=f.read())

# @app.get("/auth/callback")
# async def callback(request: Request):
#     print(request.query_params)
#     code = request.query_params.get("code")
#     if not code:
#         return {"error": "Missing authorization code"}
#     # Here, you would handle token exchange if needed
#     return {"message": "Login successful!", "code": code}

@app.get("/")
async def root():
    
    return {"message": "Hello from SmartGreen!"}

# if __name__ == "__main__":
#     uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

@app.get('/api/users')
def get_users():
    users = [
        {"id": 1, "name": "John Doe"},
        {"id": 2, "name": "Jane Smith"},
    ]
    return users

@app.get('/api/tools')
def get_tools():
    tools = [
        {"id": 1, "name": "Cangkul"},
        {"id": 2, "name": "Pupuk"},
        {"id": 3, "name": "Sprayer"},
    ]
    return tools

# if __name__ == '__main__':
#     app.run()
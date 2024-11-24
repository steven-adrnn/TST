import uvicorn
import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)




@app.get("/auth/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "Missing authorization code"}
    # Here, you would handle token exchange if needed
    return {"message": "Login successful!"}

@app.get("/")
async def root():
    
    return {"message": "Hello from SmartGreen!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

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

if __name__ == '__main__':
    app.run()
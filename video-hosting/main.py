from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from database import supabase
from models import User, Video, Comment, Complaint
from datetime import datetime
import uuid

app = FastAPI(title="Видеохостинг для обучения")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Глобальная переменная для хранения текущего пользователя (упрощенно)
current_user = None

# === Страницы ===
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    videos = supabase.table("videos").select("*").execute()
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "videos": videos.data,
        "user": current_user
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/video/{video_id}", response_class=HTMLResponse)
async def video_page(request: Request, video_id: str):
    video = supabase.table("videos").select("*").eq("id", video_id).execute()
    comments = supabase.table("comments").select("*").eq("video_id", video_id).execute()
    
    if not video.data:
        raise HTTPException(status_code=404, detail="Видео не найдено")
    
    return templates.TemplateResponse("video.html", {
        "request": request,
        "video": video.data[0],
        "comments": comments.data,
        "user": current_user
    })

@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    if not current_user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("upload.html", {"request": request, "user": current_user})

# === API endpoints ===
@app.post("/api/register")
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    # Проверка, существует ли пользователь
    existing = supabase.table("users").select("*").eq("email", email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")
    
    user_id = str(uuid.uuid4())
    user_data = {
        "id": user_id,
        "username": username,
        "email": email,
        "password": password,  # В реальном проекте нужно хешировать!
        "created_at": datetime.now().isoformat()
    }
    
    result = supabase.table("users").insert(user_data).execute()
    global current_user
    current_user = user_data
    return RedirectResponse("/", status_code=303)

@app.post("/api/login")
async def login(
    email: str = Form(...),
    password: str = Form(...)
):
    user = supabase.table("users").select("*").eq("email", email).eq("password", password).execute()
    
    if not user.data:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    global current_user
    current_user = user.data[0]
    return RedirectResponse("/", status_code=303)

@app.get("/api/logout")
async def logout():
    global current_user
    current_user = None
    return RedirectResponse("/", status_code=303)

@app.post("/api/upload")
async def upload_video(
    title: str = Form(...),
    description: str = Form(...),
    url: str = Form(...)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Необходима авторизация")
    
    video_data = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "url": url,
        "user_id": current_user["id"],
        "views": 0,
        "likes": 0,
        "dislikes": 0,
        "created_at": datetime.now().isoformat()
    }
    
    supabase.table("videos").insert(video_data).execute()
    return RedirectResponse("/", status_code=303)

@app.post("/api/comment/{video_id}")
async def add_comment(
    video_id: str,
    content: str = Form(...)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Необходима авторизация")
    
    comment_data = {
        "id": str(uuid.uuid4()),
        "content": content,
        "user_id": current_user["id"],
        "username": current_user["username"],
        "video_id": video_id,
        "created_at": datetime.now().isoformat()
    }
    
    supabase.table("comments").insert(comment_data).execute()
    return RedirectResponse(f"/video/{video_id}", status_code=303)

@app.post("/api/like/{video_id}")
async def like_video(video_id: str):
    if not current_user:
        return {"error": "Unauthorized"}
    
    video = supabase.table("videos").select("*").eq("id", video_id).execute()
    if video.data:
        new_likes = video.data[0].get("likes", 0) + 1
        supabase.table("videos").update({"likes": new_likes}).eq("id", video_id).execute()
    return RedirectResponse(f"/video/{video_id}", status_code=303)

@app.post("/api/dislike/{video_id}")
async def dislike_video(video_id: str):
    if not current_user:
        return {"error": "Unauthorized"}
    
    video = supabase.table("videos").select("*").eq("id", video_id).execute()
    if video.data:
        new_dislikes = video.data[0].get("dislikes", 0) + 1
        supabase.table("videos").update({"dislikes": new_dislikes}).eq("id", video_id).execute()
    return RedirectResponse(f"/video/{video_id}", status_code=303)

@app.post("/api/complaint/{video_id}")
async def file_complaint(
    video_id: str,
    reason: str = Form(...)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Необходима авторизация")
    
    complaint_data = {
        "id": str(uuid.uuid4()),
        "reason": reason,
        "user_id": current_user["id"],
        "video_id": video_id,
        "created_at": datetime.now().isoformat()
    }
    
    supabase.table("complaints").insert(complaint_data).execute()
    return RedirectResponse(f"/video/{video_id}", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
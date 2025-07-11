from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import hashlib
import base64
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Authentication Models
class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    role: str = "user"  # user or admin

class UserLogin(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Student Models
class Subject(BaseModel):
    name: str
    marks: int
    grade: str

class SemesterResult(BaseModel):
    semester: str
    subjects: List[Subject]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StudentCreate(BaseModel):
    name: str
    roll_number: str
    stream: str
    photo: Optional[str] = None  # base64 encoded image
    current_semester: str = "1"

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    roll_number: Optional[str] = None
    stream: Optional[str] = None
    photo: Optional[str] = None
    current_semester: Optional[str] = None

class Student(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    roll_number: str
    stream: str
    photo: Optional[str] = None
    current_semester: str
    semester_results: List[SemesterResult] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None

class SubjectUpdate(BaseModel):
    subjects: List[Subject]
    semester: str

# Activity Log Model
class ActivityLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str
    user_email: str
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    details: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Helper functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    return hash_password(password) == hashed_password

def calculate_grade(marks: int) -> str:
    if marks >= 90:
        return "A+"
    elif marks >= 80:
        return "A"
    elif marks >= 70:
        return "B+"
    elif marks >= 60:
        return "B"
    elif marks >= 50:
        return "C"
    elif marks >= 40:
        return "D"
    else:
        return "F"

# Authentication dependency
async def get_current_user(email: str = None):
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_doc = await db.users.find_one({"email": email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_doc)

# Initialize admin user
async def init_admin():
    admin_email = "rohan@gcet.edu.in"
    admin_password = "Rohan@95@"
    
    existing_admin = await db.users.find_one({"email": admin_email})
    if not existing_admin:
        admin_user = User(
            email=admin_email,
            name="Rohan",
            role="admin"
        )
        admin_dict = admin_user.dict()
        admin_dict["password"] = hash_password(admin_password)
        
        await db.users.insert_one(admin_dict)
        print(f"Admin user created: {admin_email}")

# Authentication Routes
@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role
    )
    
    user_dict = user.dict()
    user_dict["password"] = hash_password(user_data.password)
    
    await db.users.insert_one(user_dict)
    
    # Log activity
    activity = ActivityLog(
        action="USER_REGISTERED",
        user_email=user_data.email,
        details={"name": user_data.name, "role": user_data.role}
    )
    await db.activity_logs.insert_one(activity.dict())
    
    return {"message": "User registered successfully", "user": user}

@api_router.post("/auth/login")
async def login(login_data: UserLogin):
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc or not verify_password(login_data.password, user_doc["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = User(**user_doc)
    
    # Log activity
    activity = ActivityLog(
        action="USER_LOGIN",
        user_email=login_data.email,
        details={"name": user.name, "role": user.role}
    )
    await db.activity_logs.insert_one(activity.dict())
    
    return {"message": "Login successful", "user": user}

# Student Management Routes
@api_router.get("/students")
async def get_students(user_email: str = None):
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    students = await db.students.find().to_list(200)
    return [Student(**student) for student in students]

@api_router.post("/students")
async def create_student(student_data: StudentCreate, user_email: str = None):
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if roll number already exists
    existing_student = await db.students.find_one({"roll_number": student_data.roll_number})
    if existing_student:
        raise HTTPException(status_code=400, detail="Roll number already exists")
    
    student = Student(
        name=student_data.name,
        roll_number=student_data.roll_number,
        stream=student_data.stream,
        photo=student_data.photo,
        current_semester=student_data.current_semester,
        updated_by=user_email
    )
    
    student_dict = student.dict()
    await db.students.insert_one(student_dict)
    
    # Log activity
    activity = ActivityLog(
        action="STUDENT_CREATED",
        user_email=user_email,
        student_id=student.id,
        student_name=student.name,
        details={"roll_number": student.roll_number, "stream": student.stream}
    )
    await db.activity_logs.insert_one(activity.dict())
    
    return student

@api_router.put("/students/{student_id}")
async def update_student(student_id: str, student_data: StudentUpdate, user_email: str = None):
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    existing_student = await db.students.find_one({"id": student_id})
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    update_data = {k: v for k, v in student_data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = user_email
    
    await db.students.update_one({"id": student_id}, {"$set": update_data})
    
    # Log activity
    activity = ActivityLog(
        action="STUDENT_UPDATED",
        user_email=user_email,
        student_id=student_id,
        student_name=existing_student["name"],
        details=update_data
    )
    await db.activity_logs.insert_one(activity.dict())
    
    updated_student = await db.students.find_one({"id": student_id})
    return Student(**updated_student)

@api_router.delete("/students/{student_id}")
async def delete_student(student_id: str, user_email: str = None):
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if user is admin
    user_doc = await db.users.find_one({"email": user_email})
    if not user_doc or user_doc["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete students")
    
    existing_student = await db.students.find_one({"id": student_id})
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    await db.students.delete_one({"id": student_id})
    
    # Log activity
    activity = ActivityLog(
        action="STUDENT_DELETED",
        user_email=user_email,
        student_id=student_id,
        student_name=existing_student["name"],
        details={"roll_number": existing_student["roll_number"]}
    )
    await db.activity_logs.insert_one(activity.dict())
    
    return {"message": "Student deleted successfully"}

@api_router.put("/students/{student_id}/subjects")
async def update_student_subjects(student_id: str, subject_data: SubjectUpdate, user_email: str = None):
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    existing_student = await db.students.find_one({"id": student_id})
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Calculate grades for subjects
    for subject in subject_data.subjects:
        subject.grade = calculate_grade(subject.marks)
    
    # Create new semester result
    semester_result = SemesterResult(
        semester=subject_data.semester,
        subjects=subject_data.subjects
    )
    
    # Update student's semester results
    student_obj = Student(**existing_student)
    
    # Remove existing result for this semester if it exists
    student_obj.semester_results = [sr for sr in student_obj.semester_results if sr.semester != subject_data.semester]
    
    # Add new result
    student_obj.semester_results.append(semester_result)
    student_obj.updated_at = datetime.utcnow()
    student_obj.updated_by = user_email
    
    await db.students.update_one({"id": student_id}, {"$set": student_obj.dict()})
    
    # Log activity
    activity = ActivityLog(
        action="STUDENT_SUBJECTS_UPDATED",
        user_email=user_email,
        student_id=student_id,
        student_name=existing_student["name"],
        details={"semester": subject_data.semester, "subjects_count": len(subject_data.subjects)}
    )
    await db.activity_logs.insert_one(activity.dict())
    
    return {"message": "Subjects updated successfully"}

# User Management Routes (Admin only)
@api_router.get("/users")
async def get_users(user_email: str = None):
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if user is admin
    user_doc = await db.users.find_one({"email": user_email})
    if not user_doc or user_doc["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view users")
    
    users = await db.users.find({}, {"password": 0}).to_list(1000)
    return [User(**user) for user in users]

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, user_email: str = None):
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if user is admin
    user_doc = await db.users.find_one({"email": user_email})
    if not user_doc or user_doc["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")
    
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow admin to delete themselves
    if target_user["email"] == user_email:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    await db.users.delete_one({"id": user_id})
    
    # Log activity
    activity = ActivityLog(
        action="USER_DELETED",
        user_email=user_email,
        details={"deleted_user": target_user["email"], "deleted_name": target_user["name"]}
    )
    await db.activity_logs.insert_one(activity.dict())
    
    return {"message": "User deleted successfully"}

@api_router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role_data: dict, user_email: str = None):
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if user is admin
    user_doc = await db.users.find_one({"email": user_email})
    if not user_doc or user_doc["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update user roles")
    
    target_user = await db.users.find_one({"id": user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_role = role_data.get("role")
    if new_role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    await db.users.update_one({"id": user_id}, {"$set": {"role": new_role}})
    
    # Log activity
    activity = ActivityLog(
        action="USER_ROLE_UPDATED",
        user_email=user_email,
        details={"target_user": target_user["email"], "old_role": target_user["role"], "new_role": new_role}
    )
    await db.activity_logs.insert_one(activity.dict())
    
    return {"message": "User role updated successfully"}

@api_router.put("/users/profile")
async def update_profile(profile_data: dict, user_email: str = None):
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_doc = await db.users.find_one({"email": user_email})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    current_password = profile_data.get("currentPassword")
    if not current_password or not verify_password(current_password, user_doc["password"]):
        raise HTTPException(status_code=400, detail="Invalid current password")
    
    # Update profile data
    update_data = {}
    if "name" in profile_data:
        update_data["name"] = profile_data["name"]
    if "email" in profile_data:
        # Check if new email is already taken
        if profile_data["email"] != user_email:
            existing_user = await db.users.find_one({"email": profile_data["email"]})
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already in use")
        update_data["email"] = profile_data["email"]
    if "newPassword" in profile_data and profile_data["newPassword"]:
        update_data["password"] = hash_password(profile_data["newPassword"])
    
    await db.users.update_one({"email": user_email}, {"$set": update_data})
    
    # Log activity
    activity = ActivityLog(
        action="PROFILE_UPDATED",
        user_email=user_email,
        details={"updated_fields": list(update_data.keys())}
    )
    await db.activity_logs.insert_one(activity.dict())
    
    return {"message": "Profile updated successfully"}

# Activity Logs (Admin only)
@api_router.get("/activity-logs")
async def get_activity_logs(user_email: str = None):
    if not user_email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if user is admin
    user_doc = await db.users.find_one({"email": user_email})
    if not user_doc or user_doc["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view activity logs")
    
    logs = await db.activity_logs.find().sort("timestamp", -1).to_list(100)
    return [ActivityLog(**log) for log in logs]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_admin()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
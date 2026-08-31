"""
Baza ulanishi va modellar.

Standart holatda SQLite fayl (xodimlar.db) ishlatiladi — hech qanday
sozlashsiz darhol ishlaydi (Streamlit Cloud'da ham). PostgreSQL'ga
o'tish uchun DATABASE_URL muhit o'zgaruvchisini belgilang, masalan:
    postgresql+psycopg2://user:password@host:5432/dbname
"""
import os
import uuid
import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, Boolean, DateTime, Date,
    Numeric, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///xodimlar.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()


def gen_id():
    return str(uuid.uuid4())


class Region(Base):
    __tablename__ = "regions"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    schools = relationship("School", back_populates="region", cascade="all, delete-orphan")


class School(Base):
    __tablename__ = "schools"
    id = Column(String, primary_key=True, default=gen_id)
    region_id = Column(String, ForeignKey("regions.id"), nullable=False)
    name = Column(String(255), nullable=False)
    address = Column(Text)
    director = Column(String(255))
    phone = Column(String(32))
    students_count = Column(Integer, default=0)
    status = Column(String(16), default="active")            # active | paused
    teacher_status = Column(String(16))                       # bor | vakant
    internet_status = Column(String(16))                      # ok | warn | bad | none
    internet_speed = Column(Numeric)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    region = relationship("Region", back_populates="schools")
    teachers = relationship("Teacher", back_populates="school", cascade="all, delete-orphan")


class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(String, primary_key=True, default=gen_id)
    school_id = Column(String, ForeignKey("schools.id"), nullable=False)
    last_name = Column(String(255))
    first_name = Column(String(255))
    middle_name = Column(String(255))
    birth_date = Column(Date)
    gender = Column(String(16))                # Erkak | Ayol
    phone = Column(String(32))
    education = Column(String(64))
    category = Column(String(64))
    certificate = Column(String(64))
    work_type = Column(String(16))             # asosiy | ichki | tashqi
    photo_url = Column(Text)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    school = relationship("School", back_populates="teachers")


class ArchiveTeacher(Base):
    __tablename__ = "archive_teachers"
    id = Column(String, primary_key=True, default=gen_id)
    original_teacher_id = Column(String)
    school_id = Column(String, ForeignKey("schools.id"))
    full_name = Column(String(255))
    data_snapshot = Column(Text)   # JSON matn sifatida saqlanadi
    archived_at = Column(DateTime, default=datetime.datetime.utcnow)
    archived_by = Column(String, ForeignKey("users.id"))


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_id)
    login = Column(String(64), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)   # bcrypt hash — hech qachon ochiq parol emas
    role = Column(String(16), nullable=False)       # superadmin | boshqarma | hudud_admin | maktab | oqituvchi
    full_name = Column(String(255))
    region_id = Column(String, ForeignKey("regions.id"), nullable=True)
    school_id = Column(String, ForeignKey("schools.id"), nullable=True)
    teacher_id = Column(String, ForeignKey("teachers.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String(64), nullable=False)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()

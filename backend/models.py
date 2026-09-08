from sqlalchemy import Column, Integer, String, Float, Date, Time, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
from pgvector.sqlalchemy import Vector


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String, nullable=False)
    sinif = Column(String, nullable=False)
    alan = Column(String, nullable=False)
    kullanici_adi = Column(String, unique=True, nullable=False)
    sifre_hash = Column(String, nullable=False)

    coach_id = Column(Integer, ForeignKey("coaches.id"))

    coach = relationship("Coach", back_populates="students")
    exam_results = relationship("ExamResult", back_populates="student")
    schedules = relationship("Schedule", back_populates="student")
    appointments = relationship("Appointment", back_populates="student")


class Coach(Base):
    __tablename__ = "coaches"

    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String, nullable=False)

    students = relationship("Student", back_populates="coach")
    appointments = relationship("Appointment", back_populates="coach")


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String, nullable=False)   # örn "Matematik"


class ExamResult(Base):
    __tablename__ = "exam_results"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    sinav_adi = Column(String, nullable=False)   # örn "TYT Deneme 3"
    net = Column(Float, nullable=False)
    tarih = Column(Date, nullable=False)

    student = relationship("Student", back_populates="exam_results")
    subject = relationship("Subject")


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    gun = Column(String, nullable=False)   # örn "Pazartesi"
    saat = Column(Time, nullable=False)

    student = relationship("Student", back_populates="schedules")
    subject = relationship("Subject")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    tarih = Column(Date, nullable=False)
    saat = Column(Time, nullable=False)
    durum = Column(String, default="confirmed")   # confirmed / cancelled
    __table_args__ = (
        UniqueConstraint("coach_id", "tarih", "saat", name="uq_coach_tarih_saat"),
    ) #race condition durumunu bu şekilde engelledik


    student = relationship("Student", back_populates="appointments")
    coach = relationship("Coach", back_populates="appointments")

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(String, nullable=False)          # anlamlı etiket, örn "devamsizlik"
    icerik = Column(String, nullable=False)
    embedding = Column(Vector(768))
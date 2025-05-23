from datetime import date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class Client(db.Model):
    __tablename__ = "client"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    tz = Column(String(9))
    birth_date = Column(Date)
    phone = Column(String(20))
    address = Column(String(200))
    gender = Column(String(10))  # Added gender field for eligibility age calculation

class Grant(db.Model):
    __tablename__ = "grant"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("client.id"))
    employer_name = Column(String(200))
    work_start_date = Column(Date)
    work_end_date = Column(Date)
    grant_amount = Column(Float)  # נומינלי
    grant_date = Column(Date)
    grant_indexed_amount = Column(Float)  # סכום מוצמד
    grant_ratio = Column(Float)  # חלק יחסי
    impact_on_exemption = Column(Float)  # פגיעה בתקרה

    client = relationship("Client", backref="grants")

class Pension(db.Model):
    __tablename__ = "pension"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("client.id"))
    payer_name = Column(String(200))
    start_date = Column(Date)  # תחילת קצבה

    client = relationship("Client", backref="pensions")

class Commutation(db.Model):
    __tablename__ = "commutation"

    id = Column(Integer, primary_key=True)
    pension_id = Column(Integer, ForeignKey("pension.id"))
    amount = Column(Float)
    date = Column(Date)
    full_or_partial = Column(String(10))  # "full" / "partial"

    pension = relationship("Pension", backref="commutations")

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
    
    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "tz": self.tz,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "phone": self.phone,
            "address": self.address,
            "gender": self.gender
        }

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
    
    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "employer_name": self.employer_name,
            "work_start_date": self.work_start_date.isoformat() if self.work_start_date else None,
            "work_end_date": self.work_end_date.isoformat() if self.work_end_date else None,
            "grant_amount": self.grant_amount,
            "grant_date": self.grant_date.isoformat() if self.grant_date else None,
            "grant_indexed_amount": self.grant_indexed_amount,
            "grant_ratio": self.grant_ratio,
            "impact_on_exemption": self.impact_on_exemption
        }

class Pension(db.Model):
    __tablename__ = "pension"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("client.id"))
    payer_name = Column(String(200))
    start_date = Column(Date)  # תחילת קצבה

    client = relationship("Client", backref="pensions")
    
    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "payer_name": self.payer_name,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "commutations": [c.to_dict() for c in self.commutations] if hasattr(self, 'commutations') else []
        }

class Commutation(db.Model):
    __tablename__ = "commutation"

    id = Column(Integer, primary_key=True)
    pension_id = Column(Integer, ForeignKey("pension.id"))
    amount = Column(Float)
    date = Column(Date)
    full_or_partial = Column(String(10))  # "full" / "partial"

    pension = relationship("Pension", backref="commutations")
    
    def to_dict(self):
        return {
            "id": self.id,
            "pension_id": self.pension_id,
            "amount": self.amount,
            "date": self.date.isoformat() if self.date else None,
            "full_or_partial": self.full_or_partial
        }

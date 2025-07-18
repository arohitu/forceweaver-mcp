from . import db
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class Customer(db.Model):
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    api_key = relationship("APIKey", uselist=False, back_populates="customer", cascade="all, delete-orphan")
    salesforce_connection = relationship("SalesforceConnection", uselist=False, back_populates="customer", cascade="all, delete-orphan")

class APIKey(db.Model):
    id = Column(Integer, primary_key=True)
    hashed_key = Column(String(255), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey('customer.id'), nullable=False)
    customer = relationship("Customer", back_populates="api_key")

class SalesforceConnection(db.Model):
    id = Column(Integer, primary_key=True)
    salesforce_org_id = Column(String(100), unique=True, nullable=False)
    encrypted_refresh_token = Column(String(512), nullable=False)
    instance_url = Column(String(255), nullable=False)
    customer_id = Column(Integer, ForeignKey('customer.id'), nullable=False)
    customer = relationship("Customer", back_populates="salesforce_connection")
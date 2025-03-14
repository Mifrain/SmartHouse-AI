from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from bot.db.base import Base
import copy

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    type = Column(String, unique=True, nullable=False)
    params = Column(JSON, nullable=True)

    #пример params: {'brightness': "100%"} или {"voltage": "220"}

class UserDevices(Base):
    __tablename__ = "user_devices"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    name = Column(String, nullable=False)
    params = Column(JSON, nullable=True)

    user = relationship("User", backref="user_devices")
    device = relationship("Device", backref="user_devices")

    def __init__(self, user_id, device_id, name, params=None):
        self.user_id = user_id
        self.device_id = device_id
        self.name = name
        # Если параметры не переданы, то берем дефолтные из девайса
        self.params = params or {}

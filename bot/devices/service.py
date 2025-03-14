from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from bot.db.base import async_session_maker
from bot.devices.model import Device, UserDevices
from bot.users.model import UserSession
from bot.db.service import BaseService

class DeviceService(BaseService):
    model = Device

    @staticmethod
    async def get_available_devices():
        async with async_session_maker() as session:
            result = await session.execute(select(Device))
            return result.scalars().all()

    @staticmethod
    async def get_user_devices(tg_id: int):
        async with async_session_maker() as session:
            query = (
                select(UserDevices)
                .join(UserSession, UserDevices.user_id == UserSession.user_id)
                .filter(UserSession.tg_id == tg_id)
            )
            result = await session.execute(query)

            return result.scalars().all()

    @staticmethod
    async def get_device_by_id(device_id: int):
        async with async_session_maker() as session:
            query = select(Device).filter(Device.id == device_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_my_device_by_id(device_id: int):
        async with async_session_maker() as session:
            query = select(UserDevices).filter_by(id = device_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_default_params(device_id: int):
        async with async_session_maker() as session:
            query = select(Device.params).filter_by(id = device_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def add_user_device(user_id: int, device_id: int, name: str):
        async with async_session_maker() as session:
            default_params = await DeviceService.get_default_params(device_id)
            new_device = UserDevices(user_id=user_id, device_id=device_id, name=name, params=default_params)
            session.add(new_device)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise ValueError("❌ Устройство с таким именем уже добавлено.")

    @staticmethod
    async def update_device_state(device_id: int, params: dict):
        async with async_session_maker() as session:
            query = select(UserDevices).filter_by(id=device_id)
            result = await session.execute(query)
            device = result.scalars().first()

            if device:
                device.params = params
                await session.commit()

    @staticmethod
    async def remove_user_device(device_id: int):
        async with async_session_maker() as session:
            query = select(UserDevices).filter_by(id=device_id)
            result = await session.execute(query)
            user_device = result.scalars().first()

            if user_device:
                await session.delete(user_device)
                await session.commit()
                return True
            else:
                return False
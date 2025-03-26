from sqlalchemy import insert, select, exists, update, delete
from passlib.hash import bcrypt

from bot.db.service import BaseService
from bot.users.model import User, UserSession
from bot.db.base import async_session_maker


class UserService(BaseService):
    model = User

    @staticmethod
    async def user_exists(login: str) -> bool:
        async with async_session_maker() as session:
            query = select(exists().where(User.login == login))
            result = await session.execute(query)
            return result.scalar()

    @staticmethod
    async def verify_password(login: str, password: str) -> bool:
        async with async_session_maker() as session:
            query = select(User).filter_by(login=login)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            return user and bcrypt.verify(password, user.password)

    @staticmethod
    async def create_user(login: str, password: str, tg_id: int):
        async with async_session_maker() as session:
            new_user = User(login=login, password=bcrypt.hash(password))
            session.add(new_user)
            await session.flush()

            new_device = UserSession(user_id=new_user.id, tg_id=tg_id)
            session.add(new_device)

            await session.commit()

    @staticmethod
    async def get_user_by_tg_id(tg_id: int):
        async with async_session_maker() as session:
            query = select(User).join(UserSession).filter(UserSession.tg_id == tg_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def add_device_to_user(login: str, tg_id: int):
        async with async_session_maker() as session:
            query = select(User).filter_by(login=login)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if user:
                new_device = UserSession(user_id=user.id, tg_id=tg_id)
                session.add(new_device)
                await session.commit()

    @staticmethod
    async def change_login(user_id: int, new_login: str) -> bool:
        async with async_session_maker() as session:
            if await UserService.user_exists(new_login):
                return False  # Логин уже занят

            query = update(User).where(User.id == user_id).values(login=new_login)
            await session.execute(query)
            await session.commit()
            return True

    @staticmethod
    async def change_password(user_id: int, old_psw: str, new_psw: str) -> bool:
        async with async_session_maker() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()

            if not user or not bcrypt.verify(old_psw, user.password):
                return False

            query = update(User).where(User.id == user_id).values(password=bcrypt.hash(new_psw))
            await session.execute(query)
            await session.commit()
            return True

    @staticmethod
    async def delete_session(user_id: int):
        async with async_session_maker() as session:
            query = delete(UserSession).where(UserSession.user_id == user_id)
            await session.execute(query)
            await session.commit()

    @staticmethod
    async def change_voice_on(tg_id: int, change: bool):
        async with async_session_maker() as session:
            query = select(User).join(UserSession).filter(UserSession.tg_id == tg_id)
            result = await session.execute(query)
            user = result.scalars().first()

            user.voice_on = change
            await session.commit()

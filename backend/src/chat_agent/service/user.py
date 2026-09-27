from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from chat_agent.core.security import hash_password
from chat_agent.mapper.user import create_user as insert_user
from chat_agent.models.user import User


class UserAlreadyExistsError(Exception):
    """用户名或邮箱已经存在。"""


async def register_user(
    session: AsyncSession,
    *,
    username: str,
    email: str,
    password: str,
) -> User:
    """完成注册用户的业务流程。"""

    normalized_username = username.strip()
    normalized_email = email.strip().lower()

    # 密码哈希是相对耗时操作，放在数据库事务外执行
    password_hash = hash_password(password)

    try:
        async with session.begin():
            return await insert_user(
                session,
                username=normalized_username,
                email=normalized_email,
                password_hash=password_hash,
            )
    except IntegrityError as exc:
        raise UserAlreadyExistsError from exc
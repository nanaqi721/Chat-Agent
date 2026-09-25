


__all__ = [

]

import asyncio
from collections.abc import AsyncIterator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.src.chat_agent.core.config import get_settings

_databse_settings = get_settings().database

_engine = create_async_engine(
    _databse_settings.url, # 数据库连接地址
    echo= _databse_settings.echo,
    pool_size= _databse_settings.pool_size,
    max_overflow= _databse_settings.max_overflow,
    pool_pre_ping=True, # 从连接池借出连接之前，先检查连接是否仍然有效。
    pool_timeout= 30, # 等待连接池提供可用连接的最长时间
    pool_recycle=1800, # 连接年龄超过1800秒后，在下次借出时重建
)

_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_engine,
    # Session 在 commit() 之后，是否把已加载对象的属性标记为“过期”
    # 如果要加载新值，显式调用： await session.refresh(instance)
    expire_on_commit=False,
)

async def get_session() -> AsyncIterator[AsyncSession]:
    """
    为一次请求提供的数据库session
    :return: session
    """
    async with _session_factory() as session:
        yield session

async def check_database_connection() -> None:
    # session连接重，不涉及ORM对象和事务不用session，而用connect
    async with _engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    # print("测试运行成功了吗")

async def dispose_engine() -> None:
    """
    关闭应用释放数据库连接池
    """
    await _engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_database_connection())
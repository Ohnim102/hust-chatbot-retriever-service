from datetime import datetime
import logging
from app.auth.utils import get_password_hash
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert 
from databases import Database
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.setting.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi:db")

settings = get_settings()

# Create engine connection
engine = create_async_engine(settings.database_url, echo=True)

# Create session for interacting with database
async_session = sessionmaker(
    engine, expire_on_commit=False, autocommit=False, class_=AsyncSession
)
# Define base class for model
Base = declarative_base()

# Create database instance
database = Database(settings.database_url)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Create default User
        default_user = {
            "email": "admin@admin.vn",
            "username": "admin",
            "password": get_password_hash("123456"),
            "birthday": datetime.now(),
        }
        # Prepare the insert statement
        stmt = insert(Base.metadata.tables["users"]).values(**default_user)
        # Using on_conflict_do_update ONLY for Postgres
        stmt = stmt.on_conflict_do_update(
            index_elements=['email'],
            set_=default_user
        )
        await conn.execute(stmt)
        await conn.commit()

async def check_db_connection() -> bool:
    try:
        stmt = select(1) 
        async with engine.connect() as conn:
            result = await conn.execute(stmt)
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

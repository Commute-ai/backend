from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.sql import text

from app.core.config import settings
from app.schemas.health import ServiceHealth

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def health_check(db: Session) -> ServiceHealth:
    """Check database health."""
    try:
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            return ServiceHealth(
                healthy=True,
                message="Database connection successful",
            )
        return ServiceHealth(
            healthy=False, message="Database query returned unexpected result"
        )
    except Exception as e:  # pylint: disable=broad-except
        return ServiceHealth(
            healthy=False, message=f"Database connection failed: {str(e)}"
        )

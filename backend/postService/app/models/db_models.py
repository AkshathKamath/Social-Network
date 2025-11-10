from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Index, Date, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from datetime import datetime
import uuid

from app.db.postgres import Base

class User(Base):
    """
    User table model matching Supabase schema.
    """
    __tablename__ = "users"
    
    # Primary key - UUID
    id = Column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Authentication fields
    email = Column(Text, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    
    # Profile fields
    full_name = Column(Text, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    user_name = Column(Text, unique=True, nullable=False, index=True)
    profile_image_url = Column(Text, nullable=True)
    
    # Social counts
    followers_count = Column(Integer, default=0, nullable=True)
    following_count = Column(Integer, default=0, nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=True
    )

    def __repr__(self):
        return f"<User(id={self.id}, user_name={self.user_name}, email={self.email})>"
    

class Follow(Base):
    """
    Follow relationship table matching Supabase schema.
    """
    __tablename__ = "follows"
    
    # Primary key - UUID
    id = Column(
        PostgreSQL_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    
    # Foreign keys - UUIDs referencing users table
    follower_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    following_id = Column(
        PostgreSQL_UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=True
    )

    def __repr__(self):
        return f"<Follow(id={self.id}, follower={self.follower_id}, following={self.following_id})>"
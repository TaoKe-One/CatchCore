"""Credential related models."""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Credential(Base):
    """Credential model for weak passwords found."""

    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    protocol = Column(String, nullable=False)  # ssh, ftp, telnet, http, smb, mysql, etc.
    username = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)  # Store as hash
    port = Column(Integer, nullable=True)
    status = Column(String, default="verified", nullable=False)  # verified, invalid, revoked
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    asset = relationship("Asset", back_populates="credentials")

    def __repr__(self):
        return f"<Credential {self.protocol}://{self.username}@{self.asset_id}>"

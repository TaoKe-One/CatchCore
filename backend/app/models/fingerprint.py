"""Fingerprint related models."""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Fingerprint(Base):
    """Fingerprint model for system/service identification."""

    __tablename__ = "fingerprints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    fingerprint_type = Column(String, nullable=False, index=True)  # os, web_framework, middleware, application, etc.
    pattern = Column(String, nullable=True)  # Pattern for matching
    regex = Column(Text, nullable=True)  # Regular expression for matching
    product = Column(String, nullable=True, index=True)
    vendor = Column(String, nullable=True, index=True)
    category = Column(String, nullable=True, index=True)
    confidence = Column(Integer, default=100, nullable=False)  # 0-100
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    matches = relationship("FingerprintMatch", back_populates="fingerprint", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Fingerprint {self.name}>"


class FingerprintMatch(Base):
    """Fingerprint match record model."""

    __tablename__ = "fingerprint_matches"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    fingerprint_id = Column(Integer, ForeignKey("fingerprints.id", ondelete="CASCADE"), nullable=False, index=True)
    matched_info = Column(Text, nullable=True)  # Additional info from the match
    confidence_score = Column(Integer, default=100, nullable=False)  # 0-100
    matched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    asset = relationship("Asset", back_populates="fingerprint_matches")
    fingerprint = relationship("Fingerprint", back_populates="matches")

    def __repr__(self):
        return f"<FingerprintMatch asset_id={self.asset_id} fingerprint_id={self.fingerprint_id}>"

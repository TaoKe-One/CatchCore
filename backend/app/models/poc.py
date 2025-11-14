"""POC related models."""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class POC(Base):
    """POC (Proof of Concept) model."""

    __tablename__ = "pocs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    cve_id = Column(String, nullable=True, index=True)
    cvss_score = Column(String, nullable=True)
    severity = Column(String, nullable=True)  # critical, high, medium, low, info
    poc_type = Column(String, nullable=False)  # nuclei, custom, metasploit, etc.
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # POC script or YAML content
    source = Column(String, nullable=True)  # afrog, nuclei, custom, etc.
    author = Column(String, nullable=True)
    reference_link = Column(String, nullable=True)
    affected_product = Column(String, nullable=True)
    affected_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)  # 1 for active, 0 for inactive

    # Relationships
    tags = relationship("POCTag", back_populates="poc", cascade="all, delete-orphan")
    vulnerabilities = relationship("Vulnerability", back_populates="poc")

    def __repr__(self):
        return f"<POC {self.name}>"


class POCTag(Base):
    """POC tag model."""

    __tablename__ = "poc_tags"

    id = Column(Integer, primary_key=True, index=True)
    poc_id = Column(Integer, ForeignKey("pocs.id", ondelete="CASCADE"), nullable=False, index=True)
    tag = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    poc = relationship("POC", back_populates="tags")

    def __repr__(self):
        return f"<POCTag {self.poc_id} {self.tag}>"

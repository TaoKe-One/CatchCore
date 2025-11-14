"""Asset related models."""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Asset(Base):
    """Asset model."""

    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String, nullable=False, index=True)
    hostname = Column(String, nullable=True)
    os = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)  # active, inactive, archived
    tags = Column(String, nullable=True)  # JSON string
    department = Column(String, nullable=True)
    environment = Column(String, nullable=True)  # production, test, development
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    services = relationship("Service", back_populates="asset", cascade="all, delete-orphan")
    vulnerabilities = relationship("Vulnerability", back_populates="asset", cascade="all, delete-orphan")
    credentials = relationship("Credential", back_populates="asset", cascade="all, delete-orphan")
    fingerprint_matches = relationship("FingerprintMatch", back_populates="asset", cascade="all, delete-orphan")
    asset_groups = relationship("AssetGroup", secondary="asset_group_members", back_populates="assets")
    projects = relationship("Project", secondary="project_assets", back_populates="assets")

    def __repr__(self):
        return f"<Asset {self.ip}>"


class AssetGroup(Base):
    """Asset group model."""

    __tablename__ = "asset_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assets = relationship("Asset", secondary="asset_group_members", back_populates="asset_groups")

    def __repr__(self):
        return f"<AssetGroup {self.name}>"


class AssetGroupMember(Base):
    """Asset group member model."""

    __tablename__ = "asset_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("asset_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AssetGroupMember group_id={self.group_id} asset_id={self.asset_id}>"


class Service(Base):
    """Service model."""

    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    port = Column(Integer, nullable=False)
    protocol = Column(String, nullable=True)  # tcp, udp
    service_name = Column(String, nullable=True, index=True)
    version = Column(String, nullable=True)
    fingerprint = Column(String, nullable=True)
    state = Column(String, default="open", nullable=False)  # open, closed, filtered
    banner = Column(Text, nullable=True)
    discovered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    asset = relationship("Asset", back_populates="services")

    def __repr__(self):
        return f"<Service {self.asset_id}:{self.port}/{self.protocol}>"

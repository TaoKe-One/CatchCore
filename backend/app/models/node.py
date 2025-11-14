"""Node related models for distributed deployment."""

from sqlalchemy import Column, String, Integer, DateTime, Float
from datetime import datetime

from app.core.database import Base


class Node(Base):
    """Scan node model for distributed architecture."""

    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False, default=8000)
    status = Column(String, default="offline", nullable=False)  # online, offline, maintenance
    node_type = Column(String, default="scanner", nullable=False)  # scanner, worker, etc.
    cpu_usage = Column(Float, default=0.0, nullable=False)  # Percentage
    memory_usage = Column(Float, default=0.0, nullable=False)  # Percentage
    disk_usage = Column(Float, default=0.0, nullable=False)  # Percentage
    max_concurrent_tasks = Column(Integer, default=5, nullable=False)
    current_tasks = Column(Integer, default=0, nullable=False)
    api_version = Column(String, nullable=True)
    last_heartbeat = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Node {self.name} {self.host}:{self.port}>"

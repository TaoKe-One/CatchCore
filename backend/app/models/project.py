"""Project related models."""

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


# Association tables
project_assets = Table(
    "project_assets",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("asset_id", Integer, ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True),
)

project_tasks = Table(
    "project_tasks",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
)


class Project(Base):
    """Project model for security assessment projects."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String, default="active", nullable=False)  # active, completed, archived
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    scope = Column(Text, nullable=True)  # Description of scope
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assets = relationship("Asset", secondary=project_assets, back_populates="projects")
    tasks = relationship("Task", secondary=project_tasks, back_populates="projects")

    def __repr__(self):
        return f"<Project {self.name}>"


class ProjectAsset(Base):
    """Project asset association model (for tracking timestamps)."""

    __tablename__ = "project_asset_assignments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ProjectAsset project_id={self.project_id} asset_id={self.asset_id}>"


class ProjectTask(Base):
    """Project task association model (for tracking timestamps)."""

    __tablename__ = "project_task_assignments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ProjectTask project_id={self.project_id} task_id={self.task_id}>"

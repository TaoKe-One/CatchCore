"""Task related models."""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class TaskTypeEnum(str, enum.Enum):
    """Task type enumeration."""

    PORT_SCAN = "port_scan"
    SERVICE_IDENTIFY = "service_identify"
    FINGERPRINT = "fingerprint"
    POC_DETECTION = "poc_detection"
    PASSWORD_CRACK = "password_crack"
    DIRECTORY_SCAN = "directory_scan"
    URL_SCAN = "url_scan"
    CUSTOM = "custom"


class TaskStatusEnum(str, enum.Enum):
    """Task status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task(Base):
    """Task model."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    task_type = Column(SQLEnum(TaskTypeEnum), nullable=False)
    target_range = Column(String, nullable=False)  # IP, IP segment, or domain
    status = Column(SQLEnum(TaskStatusEnum), default=TaskStatusEnum.PENDING, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=5, nullable=False)  # 1-10, higher is more important
    scheduled_at = Column(DateTime, nullable=True)  # For scheduled tasks
    progress = Column(Integer, default=0, nullable=False)  # 0-100, progress percentage
    current_step = Column(String, nullable=True)  # Current step description
    total_steps = Column(Integer, default=0, nullable=False)  # Total steps in task

    # Relationships
    created_by_user = relationship("User", back_populates="tasks")
    configs = relationship("TaskConfig", back_populates="task", cascade="all, delete-orphan")
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")
    results = relationship("TaskResult", back_populates="task", cascade="all, delete-orphan")
    projects = relationship("Project", secondary="project_tasks", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.id} {self.task_type}>"


class TaskConfig(Base):
    """Task configuration model."""

    __tablename__ = "task_configs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    config_key = Column(String, nullable=False)
    config_value = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    task = relationship("Task", back_populates="configs")

    def __repr__(self):
        return f"<TaskConfig {self.task_id} {self.config_key}={self.config_value}>"


class TaskLog(Base):
    """Task log model."""

    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    level = Column(String, default="INFO", nullable=False)  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    task = relationship("Task", back_populates="logs")

    def __repr__(self):
        return f"<TaskLog {self.task_id} {self.level}>"


class TaskResult(Base):
    """Task result model."""

    __tablename__ = "task_results"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    result_type = Column(String, nullable=False)  # asset, service, vulnerability, etc.
    result_data = Column(JSON, nullable=False)  # Store result as JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    task = relationship("Task", back_populates="results")

    def __repr__(self):
        return f"<TaskResult {self.task_id} {self.result_type}>"

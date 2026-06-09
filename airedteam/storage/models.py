from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class TargetConfig(Base):
    __tablename__ = "target_configs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    plugin: Mapped[str] = mapped_column(String(100))
    params_json: Mapped[dict] = mapped_column(JSON, default=dict)
    secret_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class DatasetMeta(Base):
    __tablename__ = "datasets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    plugin: Mapped[str] = mapped_column(String(100))
    params_json: Mapped[dict] = mapped_column(JSON, default=dict)
    blob_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    item_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"
    __table_args__ = (UniqueConstraint("dataset_id", "version", name="uq_dataset_versions_dataset_version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    blob_path: Mapped[str] = mapped_column(String(500))
    item_count: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class PromptAssetOverride(Base):
    __tablename__ = "prompt_asset_overrides"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    asset_id: Mapped[str] = mapped_column(String(200), index=True)
    name: Mapped[str] = mapped_column(String(200))
    template_text: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class PromptAssetCustom(Base):
    __tablename__ = "prompt_assets"
    id: Mapped[str] = mapped_column(String(200), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    plugin: Mapped[str] = mapped_column(String(100), default="custom")
    purpose: Mapped[str] = mapped_column(String(200), default="custom")
    category: Mapped[str] = mapped_column(String(200), default="custom")
    variables_json: Mapped[list] = mapped_column(JSON, default=list)
    template_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200))
    runspec_yaml: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    progress_total: Mapped[int] = mapped_column(Integer, default=0)
    progress_done: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    filtered_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    kind: Mapped[str] = mapped_column(String(20), default="automated")
    attempts = relationship("Attempt", back_populates="run", cascade="all, delete-orphan")


class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id", ondelete="CASCADE"))
    target_id: Mapped[str] = mapped_column(String(100))
    target_name: Mapped[str] = mapped_column(String(200))
    dataset_item_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    work_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    original_prompt_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_text: Mapped[str] = mapped_column(Text)
    converter_chain: Mapped[list] = mapped_column(JSON, default=list)
    executor_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    executor_kind: Mapped[str | None] = mapped_column(String(40), nullable=True)
    dataset_item_language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_blob_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    conversation_blob_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    prompt_snapshot_blob_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    run = relationship("Run", back_populates="attempts")
    scores = relationship("Score", back_populates="attempt", cascade="all, delete-orphan")


class Score(Base):
    __tablename__ = "scores"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    attempt_id: Mapped[str] = mapped_column(String(36), ForeignKey("attempts.id", ondelete="CASCADE"))
    scorer: Mapped[str] = mapped_column(String(100))
    value_json: Mapped[dict] = mapped_column(JSON)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_snapshot_blob_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    reviewer_label: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    attempt = relationship("Attempt", back_populates="scores")


Index("ix_attempts_run_id", Attempt.run_id)
Index("uq_attempts_run_work_key", Attempt.run_id, Attempt.work_key, unique=True)
Index("ix_scores_attempt_id", Score.attempt_id)
Index("ix_dataset_versions_dataset_id", DatasetVersion.dataset_id)

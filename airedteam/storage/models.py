from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import (
    String, Integer, DateTime, ForeignKey, JSON, LargeBinary, Text, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class TargetConfig(Base):
    __tablename__ = "target_configs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    plugin: Mapped[str] = mapped_column(String(100))
    params_json: Mapped[dict] = mapped_column(JSON, default=dict)
    secret_ciphertext: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DatasetMeta(Base):
    __tablename__ = "datasets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    plugin: Mapped[str] = mapped_column(String(100))
    params_json: Mapped[dict] = mapped_column(JSON, default=dict)
    blob_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    item_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    attempts = relationship("Attempt", back_populates="run", cascade="all, delete-orphan")


class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id", ondelete="CASCADE"))
    target_id: Mapped[str] = mapped_column(String(100))
    target_name: Mapped[str] = mapped_column(String(200))
    dataset_item_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    prompt_text: Mapped[str] = mapped_column(Text)
    converter_chain: Mapped[list] = mapped_column(JSON, default=list)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_blob_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    conversation_blob_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    run = relationship("Run", back_populates="attempts")
    scores = relationship("Score", back_populates="attempt", cascade="all, delete-orphan")


class Score(Base):
    __tablename__ = "scores"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    attempt_id: Mapped[str] = mapped_column(String(36), ForeignKey("attempts.id", ondelete="CASCADE"))
    scorer: Mapped[str] = mapped_column(String(100))
    value_json: Mapped[dict] = mapped_column(JSON)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    attempt = relationship("Attempt", back_populates="scores")


Index("ix_attempts_run_id", Attempt.run_id)
Index("ix_scores_attempt_id", Score.attempt_id)

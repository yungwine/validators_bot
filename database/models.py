from datetime import datetime
from typing import Optional

from sqlalchemy import String, BigInteger, DateTime, ARRAY, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserModel(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # name: Mapped[str] = mapped_column(String(64))
    username: Mapped[Optional[str]] = mapped_column(String(32))
    state: Mapped[str] = mapped_column(String(128), default="")
    date_joined: Mapped[datetime] = mapped_column(DateTime)


class NodeModel(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), index=True)
    adnl: Mapped[str] = mapped_column(String(64))
    label: Mapped[Optional[str]] = mapped_column(String(64))


class AlertModel(Base):
    __tablename__ = "user_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    node_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("nodes.id"))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    alert_type: Mapped[str] = mapped_column(String(32))
    enabled: Mapped[bool] = mapped_column(default=True)

    __table_args__ = (
        Index("idx_alert_enabled", "alert_type", "user_id", "enabled"),
    )

class TriggeredAlert(Base):
    __tablename__ = "triggered_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    alert_name = mapped_column(String(32), index=True)
    timestamp = mapped_column(BigInteger)

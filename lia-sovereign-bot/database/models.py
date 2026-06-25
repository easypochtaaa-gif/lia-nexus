from sqlalchemy import BigInteger, String, Integer, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(64))
    first_name: Mapped[Optional[str]] = mapped_column(String(128))
    
    # Tariff
    tier: Mapped[str] = mapped_column(String(20), default="free")  # free/lite/pro/ultra
    premium_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Usage
    daily_requests: Mapped[int] = mapped_column(Integer, default=0)
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    last_request_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Aegis
    aegis_score: Mapped[Optional[int]] = mapped_column(Integer)
    aegis_rank: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Voice
    voice_id: Mapped[str] = mapped_column(String(50), default="neutral")
    
    # Referral
    referrer_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"))
    referrals_count: Mapped[int] = mapped_column(Integer, default=0)
    bonus_requests: Mapped[int] = mapped_column(Integer, default=0)
    
    # Antifraud
    ip_hash: Mapped[Optional[str]] = mapped_column(String(64))
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Meta
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Web3 & RPG
    wallet_address: Mapped[Optional[str]] = mapped_column(String(64))
    xp: Mapped[int] = mapped_column(Integer, default=0)
    stab_coins: Mapped[int] = mapped_column(Integer, default=0)
    
    # Settings
    daily_brief: Mapped[bool] = mapped_column(Boolean, default=True)
    language: Mapped[str] = mapped_column(String(5), default="ru")
    active_persona: Mapped[str] = mapped_column(String(20), default="sovereign")


class Memory(Base):
    __tablename__ = "memories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    key: Mapped[str] = mapped_column(String(64))  # e.g., "user_goal", "project_name"
    value: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String(20))  # user/assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Payment(Base):
    __tablename__ = "payments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    amount_uah: Mapped[float] = mapped_column(nullable=True)
    amount_usdt: Mapped[float] = mapped_column(nullable=True)
    tier: Mapped[str] = mapped_column(String(20))
    method: Mapped[str] = mapped_column(String(30))  # wayforpay/crypto
    status: Mapped[str] = mapped_column(String(20), default="pending")
    tx_hash: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Quest(Base):
    __tablename__ = "quests"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    reward_xp: Mapped[int] = mapped_column(Integer, default=0)
    reward_stab: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class UserQuest(Base):
    __tablename__ = "user_quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    quest_id: Mapped[int] = mapped_column(Integer, ForeignKey("quests.id"))
    status: Mapped[str] = mapped_column(String(20), default="active") # active, completed
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class Threat(Base):
    """AEGIS: Real security threat log"""
    __tablename__ = "threats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    threat_type: Mapped[str] = mapped_column(String(32))  # ban, spam, auth_fail, rate_limit, admin_deny, flood
    severity: Mapped[str] = mapped_column(String(16), default="medium")  # low, medium, high, critical
    source: Mapped[Optional[str]] = mapped_column(String(128))  # IP, chat_id, etc
    details: Mapped[Optional[str]] = mapped_column(Text)
    blocked: Mapped[bool] = mapped_column(Boolean, default=True)  # was action taken
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class QuestApplication(Base):
    __tablename__ = "quest_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text)
    requested_reward_xp: Mapped[int] = mapped_column(Integer, default=0)
    requested_reward_stab: Mapped[int] = mapped_column(Integer, default=0)
    conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, active, completed, rejected
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    video_stream_url: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    is_battle: Mapped[bool] = mapped_column(Boolean, default=False)
    opponent_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    territory_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ref_invite_new: Mapped[bool] = mapped_column(Boolean, default=False)


class Debate(Base):
    """SYNAPSE Triple Core: история дебатов ядер (для видео/обзоров)."""
    __tablename__ = "debates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    prompt: Mapped[str] = mapped_column(Text)
    architect: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pragmatic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    analyst: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    arbiter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Territory(Base):
    __tablename__ = "territories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    radius_km: Mapped[float] = mapped_column(Float, default=0.5)
    quest_title: Mapped[str] = mapped_column(String(128))
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MapReward(Base):
    __tablename__ = "map_rewards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    type: Mapped[str] = mapped_column(String(20), default="coin")  # coin, xp
    amount: Mapped[int] = mapped_column(Integer, default=50)
    is_collected: Mapped[bool] = mapped_column(Boolean, default=False)
    collected_by: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
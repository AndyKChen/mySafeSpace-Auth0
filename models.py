from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.sql import func

Base = declarative_base()

# User model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    first = Column(String, nullable=False)
    last = Column(String, nullable=False)

    user_info = relationship("UserInfo", back_populates="user")
    messages_sent = relationship("Message", foreign_keys='Message.sender_id', back_populates="sender")
    messages_received = relationship("Message", foreign_keys='Message.reciever_id', back_populates="reciever")
    friendships = relationship("Friendship", back_populates="user")
    attributes = relationship("Attribute", back_populates="user")


# User Info model
class UserInfo(Base):
    __tablename__ = 'user_info'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, ForeignKey('users.username'), nullable=False)
    avatar = Column(String, nullable=False, default="default")
    facebook = Column(String, default="N/A")
    twitter = Column(String, default="N/A")
    instagram = Column(String, default="N/A")

    user = relationship("User", back_populates="user_info")


# Messages (1:1 chat messages)
class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    reciever_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    time = Column(DateTime, default=func.now())
    message = Column(Text, nullable=False)
    sentiment = Column(String, nullable=False)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    reciever = relationship("User", foreign_keys=[reciever_id], back_populates="messages_received")


# Channel Messages (for group chats)
class ChannelMessage(Base):
    __tablename__ = 'channel_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(String, ForeignKey('channels.channel_id'), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    sender = Column(Integer, ForeignKey('users.id'), nullable=False)
    sender_name = Column(String, nullable=False)
    sentiment = Column(String, nullable=False)

    channel = relationship("Channel", back_populates="messages")


# Attributes (to track malicious message attributes like 'toxic', 'identity attack', etc.)
class Attribute(Base):
    __tablename__ = 'attributes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    attribute = Column(String, nullable=False)
    date = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="attributes")


# Channels (for group chats)
class Channel(Base):
    __tablename__ = 'channels'
    channel_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    topic = Column(String, nullable=True)
    picture = Column(String, default="default")

    messages = relationship("ChannelMessage", back_populates="channel")


# Chat IDs (to manage 1-on-1 chat relationships)
class ChatID(Base):
    __tablename__ = 'chat_ids'
    chat_id = Column(String, primary_key=True)
    p1_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    p2_id = Column(Integer, ForeignKey('users.id'), nullable=False)


# Friendships (for user relationships)
class Friendship(Base):
    __tablename__ = 'friendships'
    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id1 = Column(Integer, ForeignKey('users.id'), nullable=False)
    person_id2 = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="friendships")


# Apply models to database
def init_db(engine):
    Base.metadata.create_all(engine)

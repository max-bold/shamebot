from venv import create
from sqlmodel import SQLModel, Relationship, Field, create_engine, Session, select


class Member(SQLModel, table=True):
    user_id: int | None = Field(default=None, foreign_key="user.id", primary_key=True)
    chat_id: int | None = Field(default=None, foreign_key="chat.id", primary_key=True)


class Chat(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    chatname: str = Field(default="")
    members: list["User"] = Relationship(back_populates="chats", link_model=Member)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(default="")
    chats: list["Chat"] = Relationship(back_populates="members", link_model=Member)


engine = create_engine("sqlite:///sandbox/db4.db")

SQLModel.metadata.create_all(engine)

with Session(engine) as session:
    user1 = User(username="user1")
    user2 = User(username="user2")
    chat1 = Chat(chatname="chat1")
    chat2 = Chat(chatname="chat2")
    session.add(user1)
    session.add(user2)
    session.add(chat1)
    session.add(chat2)
    chat1.members.extend([user1, user2])
    chat2.members.append(user1)
    session.commit()

with Session(engine) as session:
    chat = session.exec(select(Chat).where(Chat.chatname == "chat1")).one()
    session.delete(chat)
    session.commit()

with Session(engine) as session:
    for user in session.exec(select(User)).all():
        print(f"User: {user.username}")
    for chat in session.exec(select(Chat)).all():
        print(f"Chat: {chat.chatname}")
    for member in session.exec(select(Member)).all():
        print(f"Member: user_id={member.user_id}, chat_id={member.chat_id}")
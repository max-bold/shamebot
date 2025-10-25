from enum import Enum
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from sqlalchemy import Column
from sqlalchemy.types import JSON


class ChatAdmin(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    chat_id: int = Field(foreign_key="chat.id", primary_key=True)
    is_muted: bool = Field(default=False)

    @classmethod
    def get(cls, session: Session, user_id: int, chat_id: int) -> "ChatAdmin | None":
        return session.exec(
            select(ChatAdmin).where(cls.user_id == user_id, cls.chat_id == chat_id)
        ).first()


class ChatMember(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    chat_id: int = Field(foreign_key="chat.id", primary_key=True)
    last_triger_time: float = Field(default=0.0)
    is_muted: bool = Field(default=False)

    @classmethod
    def get(cls, session: Session, user_id: int, chat_id: int) -> "ChatMember | None":
        return session.exec(
            select(ChatMember).where(cls.user_id == user_id, cls.chat_id == chat_id)
        ).first()


class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user_name: str = Field(default="")
    admin_in: list["Chat"] = Relationship(
        back_populates="admins",
        link_model=ChatAdmin,
    )
    chats: list["Chat"] = Relationship(
        back_populates="members",
        link_model=ChatMember,
    )


class Triggers(Enum):
    MESSAGE = "message"
    VIDEO = "video"
    SHORT = "short"


class Chat(SQLModel, table=True):
    id: int = Field(primary_key=True)
    chat_name: str = Field(default="")
    admins: list[User] = Relationship(
        back_populates="admin_in",
        link_model=ChatAdmin,
    )
    members: list[User] = Relationship(
        back_populates="chats",
        link_model=ChatMember,
    )
    # Store list of triggers in a JSON column since plain Python lists don't map to SQL types
    triggers: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    notify_time: float = Field(default=0.0)
    notify_max_time: float = Field(default=0.0)
    bot_is_admin: bool = Field(default=False)
    setup_complete: bool = Field(default=False)


# def get_chat_admins(session: Session, chat_id: int) -> list[User]:
#     chat = session.get(Chat, chat_id)
#     if chat:
#         return chat.admins
#     return []


# def get_chat_members(session: Session, chat_id: int) -> list[User]:
#     chat = session.get(Chat, chat_id)
#     if chat:
#         return chat.members
#     return []


# def get_chats_by_admin_id(session: Session, user_id: int) -> list[Chat]:
#     user = session.get(User, user_id)
#     if user:
#         return user.admin_in
#     return []


# def get_chats_by_member_id(session: Session, user_id: int) -> list[Chat]:
#     user = session.get(User, user_id)
#     if user:
#         return user.chats
#     return []


def members_to_notify_by_chat(
    session: Session, chat: Chat, current_time: float
) -> list[User]:
    members_to_notify = []
    for member in chat.members:
        memcership = ChatMember.get(session, member.id, chat.id)
        if (
            memcership
            and not memcership.is_muted
            and (current_time - memcership.last_triger_time) >= chat.notify_time
            and (current_time - memcership.last_triger_time) <= chat.notify_max_time
        ):
            members_to_notify.append(member)

    return members_to_notify


engine = create_engine("sqlite:///database.db")
SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    pass
    # db_init()
    # with Session(engine) as session:
    #     user1 = User(id=1, user_name="Alice")
    #     user2 = User(id=2, user_name="Bob")
    #     chat1 = Chat(id=-1, chat_name="General")
    #     chat2 = Chat(id=-2, chat_name="Random")

    #     chat1.admins.append(user1)
    #     chat1.members.extend([user1, user2])
    #     chat2.admins.append(user2)
    #     chat2.members.append(user2)

    #     session.add(user1)
    #     session.add(user2)
    #     session.add(chat1)
    #     session.add(chat2)
    #     session.commit()

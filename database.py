from enum import Enum
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from sqlalchemy import Column
from sqlalchemy.types import JSON
from aiogram.types import ContentType


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
    last_trigger_time: float = Field(default=0.0)
    last_notify_time: float = Field(default=0.0)
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
    TEXT = "text"
    VIDEO = "video"
    PHOTO = "photo"
    VOICE = "voice"
    VIDEO_NOTE = "video_note"
    ANY = "any"


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
    text_triggers: bool = Field(default=True)
    photo_triggers: bool = Field(default=True)
    video_triggers: bool = Field(default=True)
    voice_triggers: bool = Field(default=True)
    video_note_triggers: bool = Field(default=True)
    notify_time: float = Field(default=0.0)
    notify_max_time: float = Field(default=0.0)
    notify_interval: float = Field(default=0.0)
    bot_is_admin: bool = Field(default=False)
    setup_complete: bool = Field(default=False)


def members_to_notify_by_chat(
    session: Session, chat: Chat, current_time: float
) -> list[User]:
    members_to_notify = []
    for member in chat.members:
        memcership = ChatMember.get(session, member.id, chat.id)
        if (
            memcership
            and not memcership.is_muted
            and (current_time - memcership.last_trigger_time) >= chat.notify_time
            and (current_time - memcership.last_trigger_time) <= chat.notify_max_time
        ):
            members_to_notify.append(member)

    return members_to_notify


engine = create_engine("sqlite:///database.db")


def db_init() -> None:
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    db_init()
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

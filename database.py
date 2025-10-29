import os
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from sqlalchemy import BigInteger


class ChatAdmin(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True, sa_type=BigInteger)
    chat_id: int = Field(foreign_key="chat.id", primary_key=True, sa_type=BigInteger)
    is_muted: bool = Field(default=False)
    chat: "Chat" = Relationship(sa_relationship_kwargs={"viewonly": True})
    user: "User" = Relationship(sa_relationship_kwargs={"viewonly": True})

    @classmethod
    def get(cls, session: Session, user_id: int, chat_id: int) -> "ChatAdmin | None":
        return session.exec(
            select(ChatAdmin).where(cls.user_id == user_id, cls.chat_id == chat_id)
        ).first()


class ChatMember(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True, sa_type=BigInteger)
    chat_id: int = Field(foreign_key="chat.id", primary_key=True, sa_type=BigInteger)
    last_trigger_time: float = Field(default=0.0)
    last_notify_time: float = Field(default=0.0)
    is_muted: bool = Field(default=False)
    chat: "Chat" = Relationship(sa_relationship_kwargs={"viewonly": True})
    user: "User" = Relationship(sa_relationship_kwargs={"viewonly": True})

    @classmethod
    def get(cls, session: Session, user_id: int, chat_id: int) -> "ChatMember | None":
        return session.exec(
            select(ChatMember).where(cls.user_id == user_id, cls.chat_id == chat_id)
        ).first()


class User(SQLModel, table=True):
    id: int = Field(primary_key=True, sa_type=BigInteger)
    user_name: str = Field(default="")
    admin_in: list["Chat"] = Relationship(
        back_populates="admins",
        link_model=ChatAdmin,
    )
    member_in: list["Chat"] = Relationship(
        back_populates="members",
        link_model=ChatMember,
    )
    memberships: list[ChatMember] = Relationship(
        sa_relationship_kwargs={"viewonly": True}
    )
    admin_memberships: list[ChatAdmin] = Relationship(
        sa_relationship_kwargs={"viewonly": True}
    )


class Chat(SQLModel, table=True):
    id: int = Field(primary_key=True, sa_type=BigInteger)
    chat_name: str = Field(default="")
    admins: list[User] = Relationship(
        back_populates="admin_in",
        link_model=ChatAdmin,
    )
    members: list[User] = Relationship(
        back_populates="member_in",
        link_model=ChatMember,
    )
    memberships: list[ChatMember] = Relationship(
        sa_relationship_kwargs={"viewonly": True}
    )
    admin_memberships: list[ChatAdmin] = Relationship(
        sa_relationship_kwargs={"viewonly": True}
    )

    text_triggers: bool = Field(default=False)
    photo_triggers: bool = Field(default=False)
    video_triggers: bool = Field(default=False)
    voice_triggers: bool = Field(default=False)
    video_note_triggers: bool = Field(default=False)
    join_triggers: bool = Field(default=False)
    notify_time: float = Field(default=0.0)
    notify_max_time: float = Field(default=0.0)
    notify_interval: float = Field(default=0.0)
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


db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL environment variable not set")
engine = create_engine(db_url)


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

from math import log
from modulefinder import Module
from typing import Generator, TYPE_CHECKING

import sys


if TYPE_CHECKING:
    import database as db
else:
    if "streamlit" in sys.modules:
        import streamlit as st

        @st.cache_resource
        def get_models():
            import database as db

            return db

        db = get_models()
    else:
        import database as db

import aiogram.types as atypes
import logging
from time import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def db_init() -> None:
    db.SQLModel.metadata.create_all(db.engine)


def add_chat(chat: atypes.Chat) -> None:
    new_chat = db.Chat(id=chat.id, chat_name=chat.title if chat.title else "")
    logger.info(f"Adding new chat: {new_chat}")
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat.id)
        if db_chat:
            logger.info(f"Chat with id {chat.id} already exists in database.")
            return
        else:
            session.add(new_chat)
            session.commit()


def add_user(user: atypes.User) -> None:
    new_user = db.User(id=user.id, user_name=user.username if user.username else "")
    logger.info(f"Adding new user: {new_user}")
    with db.Session(db.engine) as session:
        db_user = session.get(db.User, user.id)
        if db_user:
            logger.info(f"User with id {user.id} already exists in database.")
            return
        else:
            session.add(new_user)
            session.commit()


def bot_added_to_chat(chat: atypes.Chat, user: atypes.User) -> None:
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat.id)
        if db_chat:
            logger.info(f"Chat with id {chat.id} already exists in database.")
        else:
            db_chat = db.Chat(id=chat.id, chat_name=chat.title if chat.title else "")
            session.add(db_chat)
            logger.info(f"Added new chat '@{chat.title}' to database")
        db_user = session.get(db.User, user.id)
        if db_user:
            logger.info(f"User with id {user.id} already exists in database.")
        else:
            db_user = db.User(
                id=user.id, user_name=user.username if user.username else ""
            )
            session.add(db_user)
            logger.info(f"Added new user '@{user.username}' to database.")
        if db_user not in db_chat.members:
            db_chat.members.append(db_user)
            logger.info(
                f"Added user '@{db_user.user_name}' to members of chat '@{db_chat.chat_name}'"
            )
        else:
            logger.info(
                f"User '@{db_user.user_name}' already is a member of chat '@{db_chat.chat_name}'"
            )
        session.commit()


def bot_deleted_from_chat(chat: atypes.Chat) -> None:
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat.id)
        if db_chat:
            logger.info(f"Deleting chat '@{chat.title}' from database.")
            session.delete(db_chat)
            session.commit()
        else:
            logger.info(f"Chat with id {chat.id} not found in database.")


def chat_setup_complete(chat: atypes.Chat) -> bool:
    logger.info(f"Checking if setup is complete for chat id {chat.id} - '{chat.title}'")
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat.id)
        if db_chat:
            logger.info(f"setup_complete = {db_chat.setup_complete}")
            return db_chat.setup_complete
        else:
            logger.info(f"Chat with id {chat.id} not found in database.")
            return False


def add_chat_admins(
    chat: atypes.Chat, admins: list[atypes.ResultChatMemberUnion]
) -> None:
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat.id)
        if not db_chat:
            logger.info(f"Chat with id {chat.id} not found in database.")
            return
        for admin in admins:
            if not admin.user.is_bot:
                db_user = session.get(db.User, admin.user.id)
                if not db_user:
                    db_user = db.User(
                        id=admin.user.id,
                        user_name=admin.user.username if admin.user.username else "",
                    )
                    session.add(db_user)
                    logger.info(f"Added new user: @{db_user.user_name}")
                if db_user not in db_chat.admins:
                    db_chat.admins.append(db_user)
                    logger.info(
                        f"Added admin '@{db_user.user_name}' to chat '@{db_chat.chat_name}'"
                    )
                if db_user in db_chat.members:
                    db_chat.members.remove(db_user)
                    logger.info(
                        f"Removed user '@{db_user.user_name}' from members of chat '@{db_chat.chat_name}' as now he is admin"
                    )
        session.commit()


def user_left_chat(chat_id: int, user_id: int) -> None:
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat_id)
        if not db_chat:
            logger.info(f"Chat with id {chat_id} not found in database.")
            return
        db_user = session.get(db.User, user_id)
        if not db_user:
            logger.info(f"User with id {user_id} not found in database.")
            return
        if db_user in db_chat.members:
            db_chat.members.remove(db_user)
            logger.info(
                f"Removed user '@{db_user.user_name}' from members of chat '@{db_chat.chat_name}'"
            )
        if db_user in db_chat.admins:
            db_chat.admins.remove(db_user)
            logger.info(
                f"Removed user '@{db_user.user_name}' from admins of chat '@{db_chat.chat_name}' as he left the chat"
            )
        session.commit()


def user_joined_chat(chat_id: int, user: atypes.User) -> None:
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat_id)
        if not db_chat:
            logger.info(f"Chat with id {chat_id} not found in database.")
            return
        db_user = session.get(db.User, user.id)
        if not db_user:
            db_user = db.User(
                id=user.id,
                user_name=user.username if user.username else "",
            )
            session.add(db_user)
            logger.info(f"Added new user: '@{db_user.user_name}' to database.")
        else:
            logger.info(f"User with id {user.id} already exists in database.")
        if db_user not in db_chat.members:
            # db_chat.members.append(db_user)
            membership = db.ChatMember(user_id=db_user.id, chat_id=db_chat.id)
            session.add(membership)
            logger.info(
                f"Added user '@{db_user.user_name}' to members of chat '@{db_chat.chat_name}'"
            )
            if db_chat.join_triggers:
                membership.last_trigger_time = time()
                logger.info(
                    f"Chat '@{db_chat.chat_name}' has join_triggers enabled. Setting last_trigger_time for user '@{db_user.user_name}'."
                )
        session.commit()


def promote_user_to_admin(chat_id: int, user: atypes.User) -> None:
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat_id)
        if not db_chat:
            db_chat = db.Chat(id=chat_id)
            logger.info(f"Chat with id {chat_id} not found in database.")
            return
        db_user = session.get(db.User, user.id)
        if not db_user:
            db_user = db.User(
                id=user.id,
                user_name=user.username if user.username else "",
            )
            session.add(db_user)
            logger.info(f"Added new user: '@{db_user.user_name}' to database.")
        else:
            logger.info(f"User with id {user.id} already exists in database.")
        if db_user not in db_chat.admins:
            db_chat.admins.append(db_user)
            logger.info(
                f"Promoted user '@{db_user.user_name}' to admin in chat '@{db_chat.chat_name}'"
            )
        if db_user in db_chat.members:
            db_chat.members.remove(db_user)
            logger.info(
                f"Removed user '@{db_user.user_name}' from members of chat '@{db_chat.chat_name}' as now he is admin"
            )
        session.commit()


def demote_user_to_member(chat_id: int, user: atypes.User) -> None:
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat_id)
        if not db_chat:
            logger.info(f"Chat with id {chat_id} not found in database.")
            return
        db_user = session.get(db.User, user.id)
        if not db_user:
            logger.info(f"User with id {user.id} not found in database.")
            return
        if db_user in db_chat.admins:
            db_chat.admins.remove(db_user)
            logger.info(
                f"Removed user '@{db_user.user_name}' from admins of chat '@{db_chat.chat_name}'"
            )
        if db_user not in db_chat.members:
            db_chat.members.append(db_user)
            logger.info(
                f"Added user '@{db_user.user_name}' to members of chat '@{db_chat.chat_name}'"
            )
        session.commit()


def got_message(message: atypes.Message) -> None:
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, message.chat.id)
        if not db_chat:
            logger.info(f"Chat with id {message.chat.id} not found in database.")
            return
        if message.from_user:
            db_user = session.get(db.User, message.from_user.id)
            if not db_user:
                db_user = db.User(
                    id=message.from_user.id,
                    user_name=(
                        message.from_user.username if message.from_user.username else ""
                    ),
                )
                session.add(db_user)
                logger.info(f"Added new user: '@{db_user.user_name}' to database.")
            else:
                logger.info(
                    f"User with id {message.from_user.id} already exists in database."
                )
        else:
            logger.info("Message has no from_user field.")
            return
        if db_user not in db_chat.members and db_user not in db_chat.admins:
            db_chat.members.append(db_user)
            logger.info(
                f"Added user '@{db_user.user_name}' to members of chat '@{db_chat.chat_name}'"
            )
        membership = db.ChatMember.get(session, db_user.id, db_chat.id)
        if membership:
            if (
                message.content_type == atypes.ContentType.TEXT
                and db_chat.text_triggers
            ):
                logger.info(
                    f"Message text triggers are enabled for chat '@{db_chat.chat_name}'. Updating last_trigger_time for '@{db_user.user_name}'."
                )
                membership.last_trigger_time = time()
            elif (
                message.content_type == atypes.ContentType.PHOTO
                and db_chat.photo_triggers
            ):
                logger.info(
                    f"Message photo triggers are enabled for chat '@{db_chat.chat_name}'. Updating last_trigger_time for '@{db_user.user_name}'."
                )
                membership.last_trigger_time = time()
            elif (
                message.content_type == atypes.ContentType.VIDEO
                and db_chat.video_triggers
            ):
                logger.info(
                    f"Message video triggers are enabled for chat '@{db_chat.chat_name}'. Updating last_trigger_time for '@{db_user.user_name}'."
                )
                membership.last_trigger_time = time()
            elif (
                message.content_type == atypes.ContentType.VOICE
                and db_chat.voice_triggers
            ):
                logger.info(
                    f"Message voice triggers are enabled for chat '@{db_chat.chat_name}'. Updating last_trigger_time for '@{db_user.user_name}'."
                )
                membership.last_trigger_time = time()
            elif (
                message.content_type == atypes.ContentType.VIDEO_NOTE
                and db_chat.video_note_triggers
            ):
                logger.info(
                    f"Message video_note triggers are enabled for chat '@{db_chat.chat_name}'. Updating last_trigger_time for '@{db_user.user_name}'."
                )
                membership.last_trigger_time = time()
            else:
                logger.info(
                    f"Message of type {message.content_type} does not trigger notifications for chat '@{db_chat.chat_name}'."
                )
        else:
            logger.info(
                f"User '@{db_user.user_name}' is not a member of chat '@{db_chat.chat_name}'. Nothing to trigger."
            )
        session.commit()


def get_chats_to_notify(session: db.Session) -> list[db.Chat]:
    chats = session.exec(db.select(db.Chat).where(db.Chat.notify_time > 0.0)).all()
    return list(chats)


def update_member_last_notify_time(
    session: db.Session, member_id: int, chat_id: int
) -> None:
    membership = db.ChatMember.get(session, member_id, chat_id)
    with db.Session(db.engine) as session:
        if membership:
            membership.last_notify_time = time()
            session.commit()


@contextmanager
def get_session() -> Generator[db.Session, None, None]:
    with db.Session(db.engine) as session:
        yield session
        session.commit()


def setup_test_chat(chat_id: int):
    logger.info(f"Setting up test chat with id {chat_id} in database.")
    with db.Session(db.engine) as session:
        chat = session.get(db.Chat, chat_id)
        if chat:
            chat.setup_complete = True
            chat.join_triggers = True
            chat.text_triggers = True
            chat.notify_interval = 10
            chat.notify_time = 60
            chat.notify_max_time = 600
            session.commit()
            logger.info(f"Chat with id {chat_id} marked as setup complete.")
        else:
            logger.info(f"Chat with id {chat_id} not found in database.")


def get_all_users() -> list[db.User]:
    with db.Session(db.engine) as session:
        users = session.exec(db.select(db.User)).all()
        return list(users)


def get_chats_by_admin(admin_id: int) -> list[db.Chat]:
    with db.Session(db.engine) as session:
        admin = session.get(db.User, admin_id)
        if not admin:
            logger.info(f"Admin with id {admin_id} not found in database.")
            return []
        return admin.admin_in


def get_chat(chat_id: int) -> db.Chat | None:
    with db.Session(db.engine) as session:
        chat = session.get(db.Chat, chat_id)
        return chat


def save_chat_settings(chat: db.Chat) -> bool:
    with db.Session(db.engine) as session:
        try:
            db_chat = session.get(db.Chat, chat.id)
            if not db_chat:
                logger.info(f"Chat with id {chat.id} not found in database.")
                return False
            db_chat.text_triggers = chat.text_triggers
            db_chat.photo_triggers = chat.photo_triggers
            db_chat.video_triggers = chat.video_triggers
            db_chat.voice_triggers = chat.voice_triggers
            db_chat.video_note_triggers = chat.video_note_triggers
            db_chat.join_triggers = chat.join_triggers
            db_chat.notify_time = chat.notify_time
            db_chat.notify_max_time = chat.notify_max_time
            db_chat.notify_interval = chat.notify_interval
            db_chat.setup_complete = True
            session.commit()
        except:
            return False
        return True


def get_chat_admins(chat_id: int):
    with db.Session(db.engine) as session:
        chat = session.get(db.Chat, chat_id)
        if not chat:
            logger.info(f"Chat with id {chat_id} not found in database.")
            return []
        return zip(chat.admins, chat.admin_memberships)


def save_admin_settings(settings: list, chat_id: int) -> bool:
    with db.Session(db.engine) as session:
        for row in settings:
            try:
                admin_id = row["Admin ID"]
                admin = session.get(db.User, admin_id)
                if not admin:
                    logger.info(f"Admin with id {admin_id} not found in database.")
                    return False
                membership = db.ChatAdmin.get(session, admin_id, chat_id)
                if not membership:
                    logger.info(
                        f"Membership for admin id {admin_id} in chat id {chat_id} not found in database."
                    )
                    return False
                membership.is_muted = row["Is Muted"]
            except Exception as e:
                logger.error(
                    f"Error updating admin settings for chat id {chat_id}: {e}"
                )
                return False
        session.commit()
        return True


def get_chat_members(chat_id: int):
    with db.Session(db.engine) as session:
        chat = session.get(db.Chat, chat_id)
        if not chat:
            logger.info(f"Chat with id {chat_id} not found in database.")
            return []
        return zip(chat.members, chat.memberships)


def save_member_settings(settings: list, chat_id: int) -> bool:
    with db.Session(db.engine) as session:
        for row in settings:
            try:
                member_id = row["Member ID"]
                membership = db.ChatMember.get(session, member_id, chat_id)
                if not membership:
                    logger.info(
                        f"Admin membership for member id {member_id} not found in database."
                    )
                    return False
                membership.is_muted = row["Is Muted"]
            except Exception as e:
                logger.error(
                    f"Error updating member settings for chat id {chat_id}: {e}"
                )
                return False
        session.commit()
        return True


def delete_chat(chat_id: int) -> bool:
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat_id)
        if not db_chat:
            logger.info(f"Chat with id {chat_id} not found in database.")
            return False
        session.delete(db_chat)
        session.commit()
        logger.info(f"Deleted chat with id {chat_id} from database.")
        return True


def get_members_to_notify_by_chat(
    session: db.Session, chat: db.Chat, current_time: float
) -> list[db.ChatMember]:
    memberships = session.exec(
        db.select(db.ChatMember).where(
            db.ChatMember.chat_id == chat.id,
            db.ChatMember.is_muted == False,
            (current_time - db.ChatMember.last_trigger_time) > chat.notify_time,
            (current_time - db.ChatMember.last_trigger_time) < chat.notify_max_time,
            (current_time - db.ChatMember.last_notify_time) > chat.notify_interval,
        )
    ).all()

    return list(memberships)

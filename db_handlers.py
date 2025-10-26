from math import log
import database as db
import aiogram.types as atypes
import logging
from time import time

logger = logging.getLogger(__name__)


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


# def delete_chat(chat: atypes.Chat) -> None:
#     with db.Session(db.engine) as session:
#         db_chat = session.get(db.Chat, chat.id)
#         if db_chat:
#             logger.info(f"Deleting chat: {db_chat}")
#             session.delete(db_chat)
#             session.commit()
#         else:
#             logger.info(f"Chat with id {chat.id} not found in database.")


def bot_added_to_chat(chat: atypes.Chat, user: atypes.User) -> None:
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat.id)
        if db_chat:
            logger.info(f"Chat with id {chat.id} already exists in database.")
        else:
            db_chat = db.Chat(id=chat.id, chat_name=chat.title if chat.title else "")
            session.add(db_chat)
            logger.info(f"Added new chat: {chat.id} - '{chat.title}' to database")
        db_user = session.get(db.User, user.id)
        if db_user:
            logger.info(f"User with id {user.id} already exists in database.")
        else:
            db_user = db.User(
                id=user.id, user_name=user.username if user.username else ""
            )
            session.add(db_user)
            logger.info(f"Added new user: {user.id} - '@{user.username}'")
        if db_user not in db_chat.members:
            db_chat.members.append(db_user)
            logger.info(
                f"Added user '@{db_user.user_name}' to chat '@{db_chat.chat_name}'"
            )
        else:
            logger.info(
                f"User '@{db_user.user_name}' already in chat '@{db_chat.chat_name}'"
            )
        session.commit()


def bot_deleted_from_chat(chat: atypes.Chat) -> None:
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat.id)
        if db_chat:
            logger.info(f"Deleting chat {chat.id} - '{chat.title}' from database.")
            session.delete(db_chat)
            session.commit()
        else:
            logger.info(f"Chat with id {chat.id} not found in database.")


def bot_is_admin_in_chat(chat: atypes.Chat) -> bool:
    logger.info(f"Checking if bot is admin in chat id {chat.id} - '{chat.title}'")
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat.id)
        if db_chat:
            logger.info(f"bot_is_admin = {db_chat.bot_is_admin}")
            return db_chat.bot_is_admin
        else:
            logger.info(f"Chat with id {chat.id} not found in database.")
            return False


def set_bot_is_admin(chat: atypes.Chat, status: bool):
    logger.info(f"Setting bot_is_admin= {status} for chat id {chat.id}")
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat.id)
        if db_chat:
            db_chat.bot_is_admin = status
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
            db_chat.members.append(db_user)
            logger.info(
                f"Added user '@{db_user.user_name}' to members of chat '@{db_chat.chat_name}'"
            )
        session.commit()


def promote_user_to_admin(chat_id: int, user: atypes.User) -> None:
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
                f"No membership record for user '@{db_user.user_name}' in chat '@{db_chat.chat_name}'. Creating new record."
            )
        session.commit()


def get_chats_to_notify(session: db.Session) -> list[db.Chat]:
    chats = session.exec(db.select(db.Chat).where(db.Chat.notify_time > 0.0)).all()
    return list(chats)


def get_members_to_notify(session: db.Session, chat: db.Chat) -> list[db.ChatMember]:
    if chat.notify_interval and chat.notify_time and chat.notify_max_time:
        ct = time()
        members = session.exec(
            db.select(db.ChatMember).where(
                db.ChatMember.chat_id == chat.id,
                db.ChatMember.is_muted == False,
                (ct - db.ChatMember.last_notify_time) >= chat.notify_interval,
                (ct - db.ChatMember.last_trigger_time) >= chat.notify_time,
                (ct - db.ChatMember.last_trigger_time) <= chat.notify_max_time,
            )
        ).all()

        return list(members)
    else:
        return []
    
def get_user_by_id(session: db.Session, user_id: int) -> db.User | None:
    return session.get(db.User, user_id)

def update_member_last_notify_time(session: db.Session, member_id: int, chat_id: int) -> None:


# def get_members_to_notify(chat: db.Chat, current_time: float) -> list[db.User]:
#     with db.Session(db.engine) as session:
#         members = session.exec(
#             db.select(db.ChatMember).where(
#                 db.ChatMember.chat_id == chat_id,
#                 db.ChatMember.is_muted == False,
#                 (time() - db.ChatMember.last_notify_time) >= chat.notify_interval,
#                 (time() - db.ChatMember.last_trigger_time) >= chat.notify_time,
#             )
#         ).all()
#         return list(members)

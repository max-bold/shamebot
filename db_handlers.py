import database as db
import aiogram.types as atypes
import logging

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
        db_user = session.get(db.User, user.id)
        if db_chat:
            logger.info(f"Chat with id {chat.id} already exists in database.")
        else:
            db_chat = db.Chat(id=chat.id, chat_name=chat.title if chat.title else "")
            session.add(db_chat)
            logger.info(f"Added new chat: {db_chat}")
        if db_user:
            logger.info(f"User with id {user.id} already exists in database.")
        else:
            db_user = db.User(
                id=user.id, user_name=user.username if user.username else ""
            )
            session.add(db_user)
            logger.info(f"Added new user: {db_user}")
        if db_user not in db_chat.members:
            db_chat.members.append(db_user)
            logger.info(f"Added user {db_user} to chat {db_chat}")
        else:
            logger.info(f"User {db_user} already in chat {db_chat}")
        session.commit()


def bot_deleted_from_chat(chat: atypes.Chat) -> None:
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat.id)
        if db_chat:
            logger.info(f"Deleting chat: {db_chat}")
            session.delete(db_chat)
            session.commit()
        else:
            logger.info(f"Chat with id {chat.id} not found in database.")


def bot_is_admin_in_chat(chat: atypes.Chat) -> bool:
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat.id)
        if db_chat:
            return db_chat.bot_is_admin
        else:
            logger.info(f"Chat with id {chat.id} not found in database.")
            return False


def set_bot_is_admin(chat: atypes.Chat, status: bool):
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat.id)
        if db_chat:
            db_chat.bot_is_admin = status
            session.commit()
        else:
            logger.info(f"Chat with id {chat.id} not found in database.")


def chat_setup_complete(chat: atypes.Chat) -> bool:
    with db.Session(db.engine) as session:
        db_chat = session.get(db.Chat, chat.id)
        if db_chat:
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
                        f"Added admin @{db_user.user_name} to chat @{db_chat.chat_name}"
                    )
        session.commit()

import asyncio
import logging
import sys
from os import getenv
from time import time

from aiogram import Bot, Dispatcher, html, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ChatMemberUpdated, Chat, chat_member_banned
from aiogram.exceptions import TelegramForbiddenError
import db_handlers as dbh
import database as db

from keys import token

import logging

logging.basicConfig(
    filename="bot.log", level=logging.INFO, encoding="utf-8", filemode="w", force=True
)
logger = logging.getLogger(__name__)

bot = Bot(token)

dp = Dispatcher()


@dp.message(CommandStart())
# Handler for the /start command
async def command_start_handler(message: Message) -> None:
    logger.info(
        f"Got '/start' command from '@{message.from_user.username if message.from_user else 'unknown'}'"
    )
    await message.answer(
        'Привет!\n\nЯ бот для управления уведомления о "спящих" участниках в групповых чатах.\n\nМеня нужно добавить в групповой чат и назначить администратором, чтобы я мог видеть сообщения участников и помогать с уведомлениями.\n\nСправишься?'
    )


@dp.message((F.text | F.photo | F.voice | F.video_note | F.video) & (F.chat.id < 0))
# Handler for media messages in group chats
async def media_handler(message: Message) -> None:
    logger.info(
        f"Got message of type {message.content_type} from '@{message.from_user.username if message.from_user else 'unknown'}' in chat '{message.chat.title}'"
    )
    dbh.got_message(message)


@dp.message(F.left_chat_member)
async def left_chat_member_handler(message: Message) -> None:
    logger.info(
        f"Got F.left_chat_member message in chat '@{message.chat.title}'. Ignoring."
    )


@dp.message(F.new_chat_members)
async def new_chat_members_handler(message: Message) -> None:
    logger.info(
        f"Got F.new_chat_members message in chat '@{message.chat.title}'. Ignoring."
    )


@dp.message(F.text & (F.chat.id > 0))
async def private_chat_message_handler(message: Message) -> None:
    logger.info(
        f"Got text message from '@{message.from_user.username if message.from_user else 'unknown'}' in private chat: {message.text}"
    )


@dp.message(~F.text & (F.chat.id > 0))
async def private_chat_non_text_message_handler(message: Message) -> None:
    logger.info(
        f"Got non-text message from '@{message.from_user.username if message.from_user else 'unknown'}' in private chat."
    )
    await message.answer(
        "Я не знаю, как на это ответить.\n\nПопробуй описать словами, что тебе нужно."
    )


@dp.message()
# Default handler for unhandled messages
async def default_message_handler(message: Message) -> None:
    logger.info(f"Unhandled message: {type(message)}: {message}")


@dp.my_chat_member(
    (F.chat.id < 0)
    & (F.new_chat_member.status == "member")
    & (F.old_chat_member.status == "administrator")
)
async def bot_demoted_handler(data: ChatMemberUpdated) -> None:
    logger.info(f"Bot lost admin rights in chat: {data.chat.id} - '{data.chat.title}'")
    try:
        await bot.send_message(
            data.from_user.id,
            f"Кажется вы удалили меня из администраторов чата {data.chat.title}!\n\nТеперь у не смогу видеть сообщения участников!",
        )
    except TelegramForbiddenError:
        logger.warning(
            f"Cannot send message to user {data.from_user.id}. They might have blocked the bot or didn't start a chat."
        )


@dp.my_chat_member((F.new_chat_member.status == "member") & (F.chat.id < 0))
# Handler for when the bot is added to a chat
async def bot_added_handler(data: ChatMemberUpdated) -> None:
    logger.info(
        f"Bot was added to chat '@{data.chat.title}' by '@{data.from_user.username}'"
    )
    try:
        await bot.send_message(
            data.from_user.id,
            f"Спасибо за добавление меня в чат '@{data.chat.title}'!\n\nТеперь меня надо назначить администратором этой группы, что-бы я мог видеть сообщения других участников.",
        )
    except TelegramForbiddenError:
        logger.warning(
            f"Cannot send message to user '@{data.from_user.id}'. They might have blocked the bot or didn't start a chat."
        )
    dbh.bot_added_to_chat(data.chat, data.from_user)
    # dbh.setup_test_chat(data.chat.id)


@dp.my_chat_member((F.new_chat_member.status == "member") & (F.chat.id > 0))
# Handler for when the bot is started in a private chat
async def bot_started_private_chat_handler(data: ChatMemberUpdated) -> None:
    logger.info(f"'@{data.from_user.username}' started private chat with bot.")


@dp.my_chat_member(F.new_chat_member.status.in_({"left", "kicked"}))
# Handler for when the bot is removed from a chat
async def bot_left_handler(data: ChatMemberUpdated) -> None:
    logger.info(
        f"Bot was kicked from chat '@{data.chat.title}' by '@{data.from_user.username}'"
    )
    try:
        await bot.send_message(
            data.from_user.id,
            f"Жаль, что вы удалили меня из чата '@{data.chat.title}'.\n\nМожете рассказать, почему?",
        )
    except TelegramForbiddenError:
        logger.warning(
            f"Cannot send message to user '@{data.from_user.id}'. They might have blocked the bot or didn't start a chat."
        )
    dbh.bot_deleted_from_chat(data.chat)


@dp.my_chat_member(F.new_chat_member.status == "administrator")
# Handler for when the bot is made an admin in a chat
async def bot_made_admin_handler(data: ChatMemberUpdated) -> None:
    logger.info(f"Bot was made admin in chat: '{data.chat.id}' - '{data.chat.title}' by '@{data.from_user.username}'")
    try:
        if not dbh.chat_setup_complete(data.chat):
            await bot.send_message(
                data.from_user.id,
                f"Ага\\! Вижу вы назначили меня администратором в чате {data.chat.title}\\! Теперь можем приступить к [настройке](http://localhost:8501/?admin={data.from_user.id})",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
        else:
            await bot.send_message(
                data.from_user.id,
                f"Спасибо, что снова сделали меня администратором в чате {data.chat.title}!",
            )
    except TelegramForbiddenError:
        logger.warning(
            f"Cannot send message to user {data.from_user.id}. They might have blocked the bot or didn't start a chat."
        )
    admins = await bot.get_chat_administrators(data.chat.id)
    dbh.add_chat_admins(data.chat, admins)
    # dbh.setup_test_chat(data.chat.id)


@dp.my_chat_member()
async def my_chat_member_handler(my_chat_member: ChatMemberUpdated) -> None:
    logger.info(
        f"Unhandled my_chat_member event: {type(my_chat_member.new_chat_member)}: {my_chat_member.new_chat_member}"
    )


@dp.chat_member(
    (F.new_chat_member.status == "member")
    & (F.old_chat_member.status == "administrator")
)
async def user_demoted_handler(data: ChatMemberUpdated) -> None:
    logger.info(
        f"User '@{data.new_chat_member.user.username}' lost 'admin' status in chat '{data.chat.title}'"
    )
    dbh.demote_user_to_member(data.chat.id, data.new_chat_member.user)


@dp.chat_member(F.new_chat_member.status == "member")
async def user_added_handler(data: ChatMemberUpdated) -> None:
    logger.info(
        f"User '@{data.new_chat_member.user.username}' was added to '@{data.chat.title}' by '@{data.from_user.username}'"
    )
    dbh.user_joined_chat(data.chat.id, data.new_chat_member.user)


@dp.chat_member(
    (F.new_chat_member.status == "kicked") | (F.new_chat_member.status == "left")
)
async def user_left_handler(data: ChatMemberUpdated) -> None:
    logger.info(
        f"User '@{data.new_chat_member.user.username}' left the chat '{data.chat.title}'"
    )
    dbh.user_left_chat(data.chat.id, data.new_chat_member.user.id)


@dp.chat_member(F.new_chat_member.status == "administrator")
async def user_made_admin_handler(data: ChatMemberUpdated) -> None:
    logger.info(
        f"User '@{data.new_chat_member.user.username}' was made admin in chat '{data.chat.title}'"
    )
    dbh.promote_user_to_admin(data.chat.id, data.new_chat_member.user)


@dp.chat_member()
async def chat_member_handler(chat_member: ChatMemberUpdated) -> None:
    logger.info(f"Unhandled chat_member event: {type(chat_member)}: {chat_member}")


async def notify_sleepy_members() -> None:
    while True:
        # logger.info("Running notify_sleepy_members task")
        with dbh.get_session() as session:
            chats = dbh.get_chats_to_notify(session)
            logger.info(f"Searching for chats to notify.")
            for chat in chats:
                logger.info(f"Checking chat '@{chat.chat_name}' for sleepy members.")
                for membership in chat.memberships:
                    if (
                        not membership.is_muted
                        and membership.last_trigger_time
                        and (time() - membership.last_trigger_time) > chat.notify_time
                        and (time() - membership.last_trigger_time)
                        < chat.notify_max_time
                        and (time() - membership.last_notify_time)
                        > chat.notify_interval
                    ):
                        logger.info(
                            f"Notifying admins about sleepy member '@{membership.user.user_name}' in chat '@{chat.chat_name}'"
                        )
                        user = membership.user
                        for admin_membership in chat.admin_memberships:
                            if not admin_membership.is_muted:
                                admin = admin_membership.user
                                try:
                                    await bot.send_message(
                                        admin.id,
                                        f"Привет! Похоже @{user.user_name} давно не проявлял активности в чате {chat.chat_name}. Напомни ему правила чата!",
                                    )
                                    logger.info(
                                        f"Notified '@{admin.user_name}' about inactivity of '@{user.user_name}' in chat '@{chat.chat_name}'"
                                    )
                                except TelegramForbiddenError:
                                    logger.warning(
                                        f"Cannot send notification to user @{admin.user_name}. They might have blocked the bot or didn't start a chat."
                                    )
                        logger.info(
                            f"Updating last_notify_time for '@{membership.user.user_name}' in chat '@{chat.chat_name}'"
                        )
                        membership.last_notify_time = time()
        await asyncio.sleep(10)


async def main() -> None:
    db.db_init()
    logger.info("Starting notify_sleepy_members task")
    asyncio.create_task(notify_sleepy_members())
    logger.info("Starting polling")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

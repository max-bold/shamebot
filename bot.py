import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, html, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ChatMemberUpdated, Chat, chat_member_banned
import db_handlers as dbh
import database as db

from keys import token

import logging

logging.basicConfig(
    filename="bot.log", level=logging.INFO, encoding="utf-8", filemode="w"
)
logger = logging.getLogger(__name__)

bot = Bot(token)

dp = Dispatcher()


@dp.message()
async def default_handler(message: Message) -> None:
    if message.text:
        logger.info(
            f"Got message: \"{message.text}\" from @{message.from_user.username if message.from_user else 'unknown'} in chat {message.chat.title}"
        )
    else:   
        logger.info(f"message: {type(message)} {message}")


@dp.my_chat_member()
async def my_chat_member_handler(my_chat_member: ChatMemberUpdated) -> None:
    if my_chat_member.new_chat_member.status == "member":
        if not dbh.bot_is_admin_in_chat(my_chat_member.chat):
            await bot.send_message(
                my_chat_member.from_user.id,
                f"Спасибо за добавление меня в чат {my_chat_member.chat.title}!\n\nТеперь меня надо назначить администратором этой группы, что-бы я мог видеть сообщения других участников.",
            )
            dbh.bot_added_to_chat(my_chat_member.chat, my_chat_member.from_user)
        else:
            await bot.send_message(
                my_chat_member.from_user.id,
                f"Кажется вы удалили меня из администраторов чата {my_chat_member.chat.title}!\n\nТеперь у не смогу видеть сообщения участников!",
            )
            dbh.set_bot_is_admin(my_chat_member.chat, False)
    elif my_chat_member.new_chat_member.status in ["left", "kicked"]:
        await bot.send_message(
            my_chat_member.from_user.id,
            f"Жаль, что вы удалили меня из чата {my_chat_member.chat.title}.\n\nМожете рассказать, почему?",
        )
        dbh.bot_deleted_from_chat(my_chat_member.chat)
    elif my_chat_member.new_chat_member.status == "administrator":
        if not dbh.chat_setup_complete(my_chat_member.chat):
            await bot.send_message(
                my_chat_member.from_user.id,
                f"Ага! Вижу вы назначили меня администратором в чате {my_chat_member.chat.title}!\n\nТеперь можем приступить к [настройке](http://link.com)",
            )
        else:
            await bot.send_message(
                my_chat_member.from_user.id,
                f"Спасибо, что снова сделали меня администратором в чате {my_chat_member.chat.title}!",
            )
        dbh.set_bot_is_admin(my_chat_member.chat, True)
        logger.info(f"Bot is now admin in chat {my_chat_member.chat.id}")
        admins = await bot.get_chat_administrators(my_chat_member.chat.id)
        dbh.add_chat_admins(my_chat_member.chat, admins)
    else:
        logger.info(
        f"Unhandled my_chat_member: {type(my_chat_member.new_chat_member)}: {my_chat_member.new_chat_member}"
    )

@dp.chat_member()
async def chat_member_handler(chat_member: ChatMemberUpdated) -> None:
    logger.info(f"chat_member: {type(chat_member)}: {chat_member}")


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    # db.db_init()
    asyncio.run(main())

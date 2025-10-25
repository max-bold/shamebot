import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.methods import SendMessage, GetChatAdministrators
from aiogram.exceptions import TelegramBadRequest

from keys import token

logging.basicConfig(
    level=logging.INFO, filename="sandbox/aio1.log", encoding="utf-8", filemode="w"
)
logger = logging.getLogger(__name__)

dp = Dispatcher()

# @dp.message(CommandStart())
# async def command_start_handler(message: Message) -> None:
#     """
#     This handler receives messages with `/start` command
#     """
#     # Most event objects have aliases for API methods that can be called in events' context
#     # For example if you want to answer to incoming message you can use `message.answer(...)` alias
#     # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
#     # method automatically or call API method directly via
#     # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
#     await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!")


@dp.message()
async def message_handler(message: Message) -> None:
    # logger.info(f"Got message: \"{message.text}\" from @{message.from_user.username} in chat {message.chat.title}")
    # logger.info(message.chat.get_administrators())
    # print(message.chat.get_administrators())
    bot = message.bot
    if bot:
        for admin in await bot.get_chat_administrators(message.chat.id):
            if not admin.user.is_bot:
                if message.text:
                    sent = await bot.send_message(
                        admin.user.id, f"Got: {message.text[:1]}"
                    )
                    for i in range(len(message.text)):
                        print(await sent.edit_text(message.text[:i]))

    # print(type(GetChatAdministrators(chat_id=message.chat.id)))
    # SendMessage(message.)


async def main() -> None:
    bot = Bot(token)
    # await dp.start_polling(bot)
    user = await bot.get_chat_member(-1003147264843,917000252)
    text = f"Это ооооооочееееннньььь длинннныыыыййййй @{user.user.username} тееееекккксссттт, кккоооторрррый перррррееееедаааеется пооооо одддддднннной буууууууквеееееее!!!!1"
    message = await bot.send_message(-1003147264843, text)
    # for i in range(2, len(text)+1):
    #     try:
    #         await message.edit_text(text[:i])
    #         await asyncio.sleep(1)
    #     except TelegramBadRequest:
    #         continue


if __name__ == "__main__":
    asyncio.run(main())

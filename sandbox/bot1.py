from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.utils.markdown import link
from keys import token

bot = Bot(token)


async def main():
    await bot.send_message(
        917000252,
        f"Привет вот {link('ссылка', 'http://127.0.0.1.nip.io:8501?admin=917000252')}",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

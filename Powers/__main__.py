import os
import asyncio
import importlib
from platform import system

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from AviaxMusic import LOGGER, app, userbot
from AviaxMusic.core.call import Aviax
from AviaxMusic.misc import sudo
from AviaxMusic.plugins import ALL_MODULES
from AviaxMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS

from Powers.bot_class import Gojo


# === uvloop setup ===
if system() == "Windows":
    LOGGER.info("Windows system detected, skipping uvloop")
else:
    LOGGER.info("Attempting to install uvloop")
    try:
        os.system("pip3 install uvloop")
        import uvloop
        uvloop.install()
        LOGGER.info("uvloop installed successfully")
    except:
        LOGGER.info("Failed to install uvloop, continuing without it")


async def init():
    # Validate assistant session strings
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("Assistant client variables not defined, exiting...")
        exit()

    await sudo()

    # Load banned users from DB
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except Exception as e:
        LOGGER("AviaxMusic").warning(f"Failed to fetch banned users: {e}")

    # Start bots
    await app.start()
    await userbot.start()

    # Load all modules
    for all_module in ALL_MODULES:
        importlib.import_module("AviaxMusic.plugins" + all_module)
    LOGGER("AviaxMusic.plugins").info("Successfully Imported Modules...")

    # Start music call handler
    await Aviax.start()
    try:
        await Aviax.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        LOGGER("AviaxMusic").error(
            "Please turn on the videochat of your log group/channel.\n\nStopping Bot..."
        )
        exit()
    except Exception:
        pass

    await Aviax.decorators()
    LOGGER("AviaxMusic").info("Aviax Music Started Successfully.")

    # Start Gojo bot
    gojo = Gojo()
    await gojo.start()   # Instead of blocking .run()

    LOGGER("Gojo").info("Gojo Bot Started Successfully.")

    # Keep both alive
    await idle()

    # Shutdown sequence
    await app.stop()
    await userbot.stop()
    await gojo.stop()
    LOGGER("AviaxMusic").info("Stopping Aviax Music + Gojo Bot...")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())

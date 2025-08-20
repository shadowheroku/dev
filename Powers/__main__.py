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


log = LOGGER(__name__)


# === uvloop setup ===
if system() == "Windows":
    log.info("Windows system detected, skipping uvloop")
else:
    log.info("Attempting to install uvloop")
    try:
        os.system("pip3 install uvloop")
        import uvloop
        uvloop.install()
        log.info("uvloop installed successfully")
    except Exception as e:
        log.info(f"Failed to install uvloop, continuing without it: {e}")


async def init():
    # Validate assistant session strings
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        log.error("Assistant client variables not defined, exiting...")
        raise SystemExit

    await sudo()

    # Load banned users from DB
    try:
        users = await get_gbanned()
        BANNED_USERS.update(users)
        users = await get_banned_users()
        BANNED_USERS.update(users)
    except Exception as e:
        log.warning(f"Failed to fetch banned users: {e}")

    # Start all clients
    await app.start()
    await userbot.start()

    gojo = Gojo()
    await gojo.start()   # if Gojo only has run(), we’ll adapt separately

    # Load Aviax plugins
    for all_module in ALL_MODULES:
        importlib.import_module("AviaxMusic.plugins" + all_module)
    log.info("Successfully Imported AviaxMusic Modules...")

    # Start music call handler
    await Aviax.start()
    try:
        await Aviax.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        log.error(
            "Please turn on the videochat of your log group/channel.\n\nStopping Bot..."
        )
        raise SystemExit
    except Exception:
        pass

    await Aviax.decorators()
    log.info("Aviax Music Started Successfully.")
    log.info("Gojo Bot Started Successfully.")

    # Keep alive until SIGINT / SIGTERM
    await idle()

    # Shutdown sequence
    await app.stop()
    await userbot.stop()
    await gojo.stop()
    log.info("Stopped Aviax Music + Gojo Bot.")


if __name__ == "__main__":
    asyncio.run(init())

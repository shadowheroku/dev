import os
import asyncio
import importlib
from platform import system

# === uvloop setup before importing Pyrogram ===
if system() != "Windows":
    try:
        import uvloop
        uvloop.install()
    except Exception as e:
        print(f"[WARN] uvloop not available: {e}")

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


async def init():
    # Validate assistant session strings
    if not any([config.STRING1, config.STRING2, config.STRING3, config.STRING4, config.STRING5]):
        log.error("Assistant client variables not defined, exiting...")
        raise SystemExit

    await sudo()

    # Load banned users from DB
    try:
        BANNED_USERS.update(await get_gbanned())
        BANNED_USERS.update(await get_banned_users())
    except Exception as e:
        log.warning(f"Failed to fetch banned users: {e}")

    # Start Pyrogram clients
    await app.start()
    await userbot.start()

    gojo = Gojo()
    await gojo.start()   # ⚠️ if only .run() exists, we’ll adapt

    # Load Aviax plugins
    for all_module in ALL_MODULES:
        importlib.import_module("AviaxMusic.plugins" + all_module)
    log.info("Successfully Imported AviaxMusic Modules...")

    # Start music call handler
    await Aviax.start()
    try:
        await Aviax.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        log.error("Please turn on the videochat of your log group/channel.\n\nStopping Bot...")
        raise SystemExit
    except Exception:
        pass

    await Aviax.decorators()
    log.info("Aviax Music Started Successfully.")
    log.info("Gojo Bot Started Successfully.")

    # Keep alive until Ctrl+C / SIGTERM
    await idle()

    # Shutdown sequence
    await app.stop()
    await userbot.stop()
    await gojo.stop()
    log.info("Stopped Aviax Music + Gojo Bot.")


if __name__ == "__main__":
    asyncio.run(init())

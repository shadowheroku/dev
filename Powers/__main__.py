import os
import asyncio
import importlib
from platform import system

# Install uvloop BEFORE Pyrogram clients
if system() != "Windows":
    try:
        import uvloop
        uvloop.install()
        print("[INFO] uvloop installed and set as default loop")
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

async def start_all():
    # Validate assistant strings
    if not any([config.STRING1, config.STRING2, config.STRING3, config.STRING4, config.STRING5]):
        log.error("Assistant client variables not defined")
        return

    await sudo()

    # Load banned users
    try:
        BANNED_USERS.update(await get_gbanned())
        BANNED_USERS.update(await get_banned_users())
    except Exception as e:
        log.warning(f"Failed to fetch banned users: {e}")

    # Start Aviax clients
    await app.start()
    await userbot.start()

    # Start Gojo in a background task
    gojo = Gojo()
    task_gojo = asyncio.create_task(gojo.run())  # if only .run() exists

    # Import plugins
    for module in ALL_MODULES:
        importlib.import_module("AviaxMusic.plugins" + module)
    log.info("AviaxMusic modules imported")

    # Start pytgcalls
    await Aviax.start()
    try:
        await Aviax.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
    except NoActiveGroupCall:
        log.error("Turn on videochat of your log group/channel")

    await Aviax.decorators()
    log.info("Aviax Music started")

    # Keep alive
    await idle()

    # Shutdown
    await app.stop()
    await userbot.stop()
    if hasattr(gojo, "stop"):
        await gojo.stop()
    else:
        task_gojo.cancel()
    log.info("All clients stopped")

# ---- MAIN ----
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_all())
    loop.run_forever()

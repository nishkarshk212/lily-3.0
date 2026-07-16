# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic
#
# Daily maintenance scheduler:
#   - Performs an automatic restart every day at DAILY_RESTART_TIME (default
#     03:00, host local time). This clears leaked memory / stale yt-dlp lock
#     files and keeps playback responsive — a stuck or bloated process is a
#     common cause of the bot "working slow".
#   - Emits an informative message to the log group before each scheduled
#     restart and on every successful boot.

import asyncio
from datetime import datetime

from ishu import app, config, logger, tasks
from ishu.plugins.restart import restart_bot


async def daily_restart_scheduler() -> None:
    # Try a few times in case the HH:MM parse is wrong before giving up.
    try:
        hr, mi = (int(x) for x in config.DAILY_RESTART_TIME.split(":"))
        assert 0 <= hr <= 23 and 0 <= mi <= 59
    except Exception:
        logger.warning(
            "Invalid DAILY_RESTART_TIME=%r — falling back to 03:00.",
            config.DAILY_RESTART_TIME,
        )
        hr, mi = 3, 0

    logger.info("Daily restart scheduler armed for %02d:%02d.", hr, mi)

    while True:
        await asyncio.sleep(30)
        now = datetime.now()
        if now.hour != hr or now.minute != mi:
            continue

        # Avoid double-firing inside the same minute: sleep past the window.
        logger.info("Scheduled daily restart triggered at %02d:%02d.", hr, mi)
        try:
            await app.send_message(
                chat_id=app.logger,
                text=(
                    f"🔄 <b>Scheduled restart</b>\n\n"
                    f"Bot: <b>{app.name}</b>\n"
                    f"Time: <code>{now.strftime('%d-%b-%y %H:%M:%S')}</code>\n\n"
                    f"Performing daily maintenance restart to keep playback "
                    f"fast and clear stale cache."
                ),
            )
        except Exception as ex:
            logger.warning("Could not send scheduled-restart notice: %s", ex)

        await asyncio.sleep(2)
        await restart_bot()


if config.DAILY_RESTART:
    tasks.append(asyncio.create_task(daily_restart_scheduler()))

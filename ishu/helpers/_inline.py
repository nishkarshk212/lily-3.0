# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import enums, types

from ishu import app, config, lang
from ishu.core.lang import lang_codes

# Per-chat cache of the last panel rows so a partial re-render (e.g. toggling
# autoplay, or the timer updater) keeps the other rows instead of clobbering
# them. Without this, the autoplay button and the progress slider fight each
# other: whichever task re-renders last wins and the other row vanishes.
_panel_state: dict[int, dict] = {}


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(
            text=text,
            callback_data=f"cancel_dl",
            style=enums.ButtonStyle.DANGER,
        )]])

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
        autoplay: bool | None = None,
    ) -> types.InlineKeyboardMarkup:
        # Reuse the last-known rows for any dimension not explicitly passed,
        # so a single-row update (timer tick OR autoplay toggle) preserves the
        # rest of the panel.
        if chat_id in _panel_state:
            prev = _panel_state[chat_id]
            if status is None:
                status = prev.get("status")
            if timer is None:
                timer = prev.get("timer")
            # None means "not explicitly passed" -> reuse cached state. An
            # explicit False (toggle OFF) must win, so only fall back on None.
            if autoplay is None and not remove:
                autoplay = prev.get("autoplay", False)

        keyboard = []
        if status:
            keyboard.append(
                [self.ikb(
                    text=status,
                    callback_data=f"controls status {chat_id}",
                    style=enums.ButtonStyle.PRIMARY,
                )]
            )
        elif timer:
            keyboard.append(
                [self.ikb(
                    text=timer,
                    callback_data=f"controls status {chat_id}",
                    style=enums.ButtonStyle.PRIMARY,
                )]
            )

        if not remove:
            keyboard.append(
                [
                    self.ikb(text="▷", callback_data=f"controls resume {chat_id}", style=enums.ButtonStyle.PRIMARY),
                    self.ikb(text="II", callback_data=f"controls pause {chat_id}", style=enums.ButtonStyle.PRIMARY),
                    self.ikb(text="⥁", callback_data=f"controls replay {chat_id}", style=enums.ButtonStyle.PRIMARY),
                    self.ikb(text="‣‣I", callback_data=f"controls skip {chat_id}", style=enums.ButtonStyle.PRIMARY),
                    self.ikb(text="▢", callback_data=f"controls stop {chat_id}", style=enums.ButtonStyle.PRIMARY),
                ]
            )
            # Autoplay toggle: green (SUCCESS) when on, red (DANGER) when off.
            # This kurigram build's ButtonStyle only has DEFAULT/PRIMARY/DANGER/
            # SUCCESS — SUCCESS is the green one. (POSITIVE/NEGATIVE don't exist.)
            # Label per user request: small-caps "ᴀᴜᴛᴏᴘʟᴀʏ" + ♾ (U+267E) when on.
            keyboard.append(
                [
                    self.ikb(
                        text=(
                            "ᴀᴜᴛᴏᴘʟᴀʏ ♾" if autoplay else "ᴀᴜᴛᴏᴘʟᴀʏ"
                        ),
                        callback_data=f"autoplay {chat_id}",
                        style=(
                            enums.ButtonStyle.SUCCESS
                            if autoplay
                            else enums.ButtonStyle.DANGER
                        ),
                    )
                ]
            )

        # Cache the resolved panel so the next partial re-render keeps these
        # rows (timer updater <-> autoplay toggle no longer clobber each other).
        _panel_state[chat_id] = {
            "status": status,
            "timer": timer,
            "autoplay": autoplay,
            "remove": remove,
        }
        return self.ikm(keyboard)

    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> types.InlineKeyboardMarkup:
        if back:
            rows = [
                [
                    self.ikb(
                        text=_lang["back"],
                        callback_data="help back",
                        style=enums.ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text=_lang["close"],
                        callback_data="help close",
                        style=enums.ButtonStyle.DANGER,
                    ),
                ]
            ]
        else:
            cbs = ["admins", "auth", "blist", "lang", "ping", "play", "queue", "stats", "sudo"]
            buttons = [
                self.ikb(text=_lang[f"help_{i}"], callback_data=f"help {cb}")
                for i, cb in enumerate(cbs)
            ]
            rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]

        return self.ikm(rows)

    def lang_markup(self, _lang: str) -> types.InlineKeyboardMarkup:
        langs = lang.get_languages()

        buttons = [
            self.ikb(
                text=f"{name} ({code})",
                callback_data=f"lang_change {code}",
                style=enums.ButtonStyle.PRIMARY if code == _lang else enums.ButtonStyle.DEFAULT,
            )
            for code, name in langs.items()
        ]
        rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
        return self.ikm(rows)

    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=text, url=config.SUPPORT_CHAT)]])

    def play_queued(
        self, chat_id: int, item_id: str, _text: str
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=_text,
                        callback_data=f"controls force {chat_id} {item_id}",
                        style=enums.ButtonStyle.PRIMARY,
                    )
                ]
            ]
        )

    def queue_markup(
        self, chat_id: int, _text: str, playing: bool
    ) -> types.InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        return self.ikm(
            [[self.ikb(text=_text, callback_data=f"controls {_action} {chat_id} q")]]
        )

    def settings_markup(
        self, lang: dict, admin_only: bool, cmd_delete: bool, language: str, chat_id: int
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=lang["play_mode"] + " ➜", callback_data="settings",
                    ),
                    self.ikb(text=admin_only, callback_data="settings play"),
                ],
                [
                    self.ikb(
                        text=lang["cmd_delete"] + " ➜", callback_data="settings",
                    ),
                    self.ikb(text=cmd_delete, callback_data="settings delete"),
                ],
                [
                    self.ikb(
                        text=lang["language"] + " ➜", callback_data="settings",
                    ),
                    self.ikb(text=lang_codes[language], callback_data="language"),
                ],
            ]
        )

    def start_key(
        self, lang: dict, private: bool = False
    ) -> types.InlineKeyboardMarkup:
        rows = [
            [
                self.ikb(
                    text=lang["add_me"],
                    url=f"https://t.me/{app.username}?startgroup=true",
                    style=enums.ButtonStyle.PRIMARY,
                )
            ],
        ]
        if private:
            rows += [
                [self.ikb(text=lang["help"], callback_data="help", style=enums.ButtonStyle.PRIMARY)],
                [
                    self.ikb(text=lang["support"], url=config.SUPPORT_CHAT, style=enums.ButtonStyle.PRIMARY),
                    self.ikb(text=lang["channel"], url=config.SUPPORT_CHANNEL, style=enums.ButtonStyle.PRIMARY),
                ]
            ]
        else:
            rows += [[self.ikb(text=lang["language"], callback_data="language", style=enums.ButtonStyle.PRIMARY)]]
        return self.ikm(rows)

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(text="❐", copy_text=link),
                    self.ikb(text="Youtube", url=link),
                ],
            ]
        )

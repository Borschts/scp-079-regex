# SCP-079-REGEX - Manage the regex patterns
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-REGEX.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from typing import Iterable, List, Optional, Union

from pyrogram import Client, InlineKeyboardMarkup, Message
from pyrogram.api.functions.messages import GetStickerSet
from pyrogram.api.types import InputStickerSetShortName, StickerSet
from pyrogram.api.types.messages import StickerSet as messages_StickerSet
from pyrogram.errors import ChatAdminRequired, ButtonDataInvalid, ChannelInvalid, ChannelPrivate, FloodWait
from pyrogram.errors import PeerIdInvalid, QueryIdInvalid

from .. import glovar
from .etc import t2t, wait_flood

# Enable logging
logger = logging.getLogger(__name__)


def answer_callback(client: Client, callback_query_id: str, text: str, show_alert: bool = False) -> Optional[bool]:
    # Answer the callback
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.answer_callback_query(
                    callback_query_id=callback_query_id,
                    text=text,
                    show_alert=show_alert
                )
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except QueryIdInvalid:
                return False
    except Exception as e:
        logger.warning(f"Answer query to {callback_query_id} error: {e}", exc_info=True)

    return result


def download_media(client: Client, file_id: str, file_ref: str, file_path: str) -> Optional[str]:
    # Download a media file
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.download_media(message=file_id, file_ref=file_ref, file_name=file_path)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
    except Exception as e:
        logger.warning(f"Download media {file_id} to {file_path} error: {e}", exc_info=True)

    return result


def edit_message_reply_markup(client: Client, cid: int, mid: int,
                              markup: InlineKeyboardMarkup = None) -> Union[bool, Message, None]:
    # Edit the message's reply markup
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.edit_message_reply_markup(
                    chat_id=cid,
                    message_id=mid,
                    reply_markup=markup
                )
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except ButtonDataInvalid:
                logger.warning(f"Edit message {mid} reply markup in {cid} - invalid markup: {markup}")
            except (ChatAdminRequired, PeerIdInvalid, ChannelInvalid, ChannelPrivate):
                return False
    except Exception as e:
        logger.warning(f"Edit message {mid} reply markup in {cid} error: {e}", exc_info=True)

    return result


def edit_message_text(client: Client, cid: int, mid: int, text: str,
                      markup: InlineKeyboardMarkup = None) -> Union[bool, Message, None]:
    # Edit the message's text
    result = None
    try:
        if not text.strip():
            return None

        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.edit_message_text(
                    chat_id=cid,
                    message_id=mid,
                    text=text,
                    parse_mode="html",
                    disable_web_page_preview=True,
                    reply_markup=markup
                )
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except ButtonDataInvalid:
                logger.warning(f"Edit message {mid} text in {cid} - invalid markup: {markup}")
            except (ChatAdminRequired, PeerIdInvalid, ChannelInvalid, ChannelPrivate):
                return False
    except Exception as e:
        logger.warning(f"Edit message {mid} in {cid} error: {e}", exc_info=True)

    return result


def get_messages(client: Client, cid: int, mids: Iterable[int]) -> List[Message]:
    # Get some messages
    result = []
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.get_messages(chat_id=cid, message_ids=mids)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
    except Exception as e:
        logger.warning(f"Get messages error: {e}", exc_info=True)

    return result


def get_sticker_title(client: Client, short_name: str, normal: bool = False, cache: bool = True) -> Optional[str]:
    # Get sticker set's title
    result = None
    try:
        result = glovar.sticker_titles.get(short_name)
        if result and cache:
            return glovar.sticker_titles[short_name]

        sticker_set = InputStickerSetShortName(short_name=short_name)
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                the_set = client.send(GetStickerSet(stickerset=sticker_set))
                if isinstance(the_set, messages_StickerSet):
                    inner_set = the_set.set
                    if isinstance(inner_set, StickerSet):
                        result = t2t(inner_set.title, normal)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)

        glovar.sticker_titles[short_name] = result
    except Exception as e:
        logger.warning(f"Get sticker {short_name} title error: {e}", exc_info=True)

    return result


def send_document(client: Client, cid: int, document: str, file_ref: str = None, caption: str = "", mid: int = None,
                  markup: InlineKeyboardMarkup = None) -> Union[bool, Message, None]:
    # Send a document to a chat
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.send_document(
                    chat_id=cid,
                    document=document,
                    file_ref=file_ref,
                    caption=caption,
                    parse_mode="html",
                    reply_to_message_id=mid,
                    reply_markup=markup
                )
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except ButtonDataInvalid:
                logger.warning(f"Send document {document} to {cid} - invalid markup: {markup}")
            except (ChatAdminRequired, PeerIdInvalid, ChannelInvalid, ChannelPrivate):
                return False
    except Exception as e:
        logger.warning(f"Send document {document} to {cid} error: {e}", exec_info=True)

    return result


def send_message(client: Client, cid: int, text: str, mid: int = None,
                 markup: InlineKeyboardMarkup = None) -> Union[bool, Message, None]:
    # Send a message to a chat
    result = None
    try:
        if not text.strip():
            return None

        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.send_message(
                    chat_id=cid,
                    text=text,
                    parse_mode="html",
                    disable_web_page_preview=True,
                    reply_to_message_id=mid,
                    reply_markup=markup
                )
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except ButtonDataInvalid:
                logger.warning(f"Send message to {cid} - invalid markup: {markup}")
            except (ChatAdminRequired, PeerIdInvalid, ChannelInvalid, ChannelPrivate):
                return False
    except Exception as e:
        logger.warning(f"Send message to {cid} error: {e}", exc_info=True)

    return result

# SCP-079-REGEX - Manage regex patterns
# Copyright (C) 2019-2020 SCP-079 <https://scp-079.org>
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
import re
from copy import deepcopy
from string import ascii_lowercase
from subprocess import run, PIPE

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import share_data, share_regex_update
from ..functions.etc import code, code_block, general_link, get_callback_data, get_command_context, get_command_type
from ..functions.etc import get_filename, get_forward_name, get_int, get_readable_time, get_text, italic, lang
from ..functions.etc import mention_id, message_link, thread
from ..functions.file import save
from ..functions.filters import from_user, regex_group, test_group
from ..functions.group import get_message
from ..functions.telegram import edit_message_text, send_message
from ..functions.tests import name_test, sticker_test, text_test
from ..functions.words import cc, get_admin, get_desc, get_match, get_same_types, same_word, word_add, words_ask
from ..functions.words import words_list, words_list_page, word_remove, words_search, words_search_page

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & Filters.command(glovar.add_commands, glovar.prefix)
                   & regex_group
                   & from_user)
def add_word(client: Client, message: Message) -> bool:
    # Add a new word
    glovar.locks["regex"].acquire()
    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id

        # Send the report message
        text, markup = word_add(client, message)
        thread(send_message, (client, cid, text, mid, markup))

        # Auto same
        word_type, word = get_command_context(message)

        if not word_type or not word:
            return True

        word_type_list = get_same_types(word)
        word_type_list.discard(word_type)

        if f"{word_type}-" in word_type_list or f"{word_type}+" in word_type_list:
            return True

        word_type_list = {w for w in word_type_list if w[-1] not in {"-", "+"}}
        same_word(client, message, "add", word, word_type_list, mid)

        return True
    except Exception as e:
        logger.warning(f"Add word error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["ask"], glovar.prefix)
                   & regex_group
                   & from_user)
def ask_word(client: Client, message: Message) -> bool:
    # Deal with a duplicated word
    glovar.locks["regex"].acquire()
    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id
        uid = message.from_user.id
        r_message = message.reply_to_message
        rid = r_message and r_message.message_id

        # Text prefix
        text = f"{lang('admin')}{lang('colon')}{mention_id(uid)}\n"

        # Check the command format
        the_type = get_command_type(message)

        if the_type in {"new", "replace", "cancel"} and r_message and r_message.from_user.is_self:
            aid = get_admin(r_message)

            if uid == aid:
                callback_data_list = get_callback_data(r_message)

                if callback_data_list and callback_data_list[0]["a"] == "ask":
                    key = callback_data_list[0]["d"]
                    ask_text = f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                    result_text, cc_list = words_ask(client, the_type, key)

                    if not result_text:
                        return True

                    ask_text += result_text
                    thread(edit_message_text, (client, cid, rid, ask_text))
                    cc(client, cc_list, aid, rid)
                    text += (f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
                             f"{lang('see')}{lang('colon')}{general_link(rid, message_link(r_message))}\n")
                else:
                    text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                             f"{lang('reason')}{lang('colon')}{code(lang('command_reply'))}\n")
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_permission'))}\n")
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code('command_usage')}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Ask word error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["captcha"], glovar.prefix)
                   & regex_group
                   & from_user)
def captcha(client: Client, message: Message) -> bool:
    # Request CAPTCHA failure data
    glovar.locks["regex"].acquire()
    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id
        aid = message.from_user.id

        # Send command
        share_data(
            client=client,
            receivers=["CAPTCHA"],
            action="captcha",
            action_type="ask",
            data={
                "admin_id": aid,
                "message_id": mid
            }
        )

        # Send the report message
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_captcha_request'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Count words error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["check"], glovar.prefix)
                   & regex_group
                   & from_user)
def check(client: Client, message: Message) -> bool:
    # Check the regex's count
    glovar.locks["regex"].acquire()
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_check'))}\n")

        # Proceed
        word_type, word = get_command_context(message)

        if word_type and word_type in glovar.regex and word:
            words = eval(f"glovar.{word_type}_words")

            text += f"{lang('type')}{lang('colon')}{code(lang(word_type))}\n"

            if glovar.comments.get(word_type):
                text += f"{lang('comment')}{lang('colon')}{code(glovar.comments[word_type])}\n"

            text += f"{lang('word')}{lang('colon')}{code(word)}\n"

            if word in words:
                count_text = (f"{italic(round(words[word]['average'], 1))} {code('/')} "
                              f"{italic(words[word]['today'])} {code('/')} "
                              f"{italic(words[word]['total'])} {code('/')} "
                              f"{italic(words[word]['temp'])}")
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
                         f"{lang('result')}{lang('colon')}{count_text}\n")
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_not_exist'))}\n")
        else:
            text += (f"{lang('type')}{lang('colon')}{code(word_type or lang('unknown'))}\n"
                     f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Check error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["comment"], glovar.prefix)
                   & regex_group
                   & from_user)
def comments_words(client: Client, message: Message) -> bool:
    # Comments words
    glovar.locks["regex"].acquire()
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_comment'))}\n")

        # Proceed
        word_type, comment = get_command_context(message)

        if word_type and word_type in {f"ad{c}" for c in ascii_lowercase} and comment:
            glovar.comments[word_type] = comment
            save("comments")

            text += f"{lang('type')}{lang('colon')}{code(lang(word_type))}\n"

            if glovar.comments.get(word_type):
                text += f"{lang('comment')}{lang('colon')}{code(glovar.comments[word_type])}\n"

            text += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
        else:
            text += (f"{lang('type')}{lang('colon')}{code(word_type or lang('unknown'))}\n"
                     f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Comments words error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["count"], glovar.prefix)
                   & regex_group
                   & from_user)
def count_words(client: Client, message: Message) -> bool:
    # Count words
    glovar.locks["regex"].acquire()
    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id
        aid = message.from_user.id

        # Choose receivers
        receivers = []

        for word_type in glovar.receivers:
            receivers += glovar.receivers[word_type]

        receivers = list(set(receivers))
        receivers.sort()

        # Send command
        share_data(
            client=client,
            receivers=receivers,
            action="regex",
            action_type="count",
            data="ask"
        )

        # Send the report message
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_count'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Count words error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["escape"], glovar.prefix)
                   & regex_group
                   & from_user)
def escape(client: Client, message: Message) -> bool:
    # Escape pattern
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_escape'))}\n")

        # Check command format
        pattern = get_command_type(message)

        # Proceed
        if pattern:
            result = re.escape(pattern)
            text += f"{lang('result')}{lang('colon')}" + "-" * 24 + "\n\n"
            text += code_block(result) + "\n"
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Escape error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(glovar.list_commands, glovar.prefix)
                   & regex_group
                   & from_user)
def list_words(client: Client, message: Message) -> bool:
    # List words
    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id

        # Send the report message
        text, markup = words_list(message)
        thread(send_message, (client, cid, text, mid, markup))

        return True
    except Exception as e:
        logger.warning(f"List words error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & Filters.command(["findall", "group", "groupdict", "groups"], glovar.prefix)
                   & test_group
                   & from_user)
def match(client: Client, message: Message) -> bool:
    # Transfer text
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        r_message = message.reply_to_message

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_match'))}\n"
                f"{lang('mode')}{lang('colon')}{code(message.command[0])}\n")

        # Check command format
        word = get_command_type(message)

        # Proceed
        if r_message and word:
            result = get_match(message.command[0], word, get_text(r_message))
            text += f"{lang('result')}{lang('colon')}" + "-" * 24 + "\n\n"
            text += code_block(result) + "\n"
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Match error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["page"], glovar.prefix)
                   & regex_group
                   & from_user)
def page_command(client: Client, message: Message) -> bool:
    # Change page
    try:
        # Basic data
        cid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id
        the_type = get_command_type(message)
        r_message = message.reply_to_message
        rid = r_message and r_message.message_id

        # Generate the report message's text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(uid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_page'))}\n")

        # Proceed
        if the_type in {"previous", "next"} and r_message and r_message.from_user.is_self:
            aid = get_admin(r_message)

            if uid == aid:
                callback_data_list = get_callback_data(r_message)
                i = (lambda x: 0 if x == "previous" else -1)(the_type)

                if callback_data_list and callback_data_list[i]["a"] in {"list", "search"}:
                    action = callback_data_list[i]["a"]
                    action_type = callback_data_list[i]["t"]
                    page = callback_data_list[i]["d"]

                    if action == "list":
                        desc = get_desc(r_message)
                        page_text, markup = words_list_page(uid, action_type, page, desc)
                    else:
                        key = action_type
                        page_text, markup = words_search_page(uid, key, page)

                    thread(edit_message_text, (client, cid, rid, page_text, markup))
                    text += (f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
                             f"{lang('see')}{lang('colon')}{general_link(rid, message_link(r_message))}\n")
                else:
                    text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                             f"{lang('reason')}{lang('colon')}{code(lang('command_reply'))}\n")
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_permission'))}\n")
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Page command error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["push"], glovar.prefix)
                   & regex_group
                   & from_user)
def push_words(client: Client, message: Message) -> bool:
    # Push words
    glovar.locks["regex"].acquire()
    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id
        uid = message.from_user.id

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{mention_id(uid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_push'))}\n")

        # Proceed
        command_type = get_command_type(message)

        if command_type in glovar.regex:
            share_regex_update(client, command_type)

            text += f"{lang('type')}{lang('colon')}{code(lang(command_type))}\n"

            if glovar.comments.get(command_type):
                text += f"{lang('comment')}{lang('colon')}{code(glovar.comments[command_type])}\n"

            text += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
        elif command_type == "all":
            for word_type in glovar.regex:
                thread(share_regex_update, (client, word_type))

            text += (f"{lang('type')}{lang('colon')}{code(lang('all'))}\n"
                     f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")
        else:
            text += (f"{lang('type')}{lang('colon')}{code(command_type or lang('unknown'))}\n"
                     f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Push words error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["regex"], glovar.prefix)
                   & test_group
                   & from_user)
def regex(client: Client, message: Message) -> bool:
    # Force regex test
    glovar.locks["regex"].acquire()
    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id
        uid = message.from_user.id
        r_message = message.reply_to_message

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{mention_id(uid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_regex'))}\n"
                f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Proceed
        if r_message:
            name_test(client, r_message)
            sticker_test(client, r_message)
            text_test(client, r_message)
            return True

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Regex error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(glovar.remove_commands, glovar.prefix)
                   & regex_group
                   & from_user)
def remove_word(client: Client, message: Message) -> bool:
    # Remove a word
    glovar.locks["regex"].acquire()
    try:
        # Basic data
        cid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id

        # Send the report message
        text, cc_list = word_remove(client, message)
        thread(send_message, (client, cid, text, mid))

        # Auto same
        word_type, word = get_command_context(message)

        if word_type and word:
            word_type_list = get_same_types(word)
            word_type_list.discard(word_type)

            if f"{word_type}-" in word_type_list or f"{word_type}+" in word_type_list:
                return True

            word_type_list = {w for w in word_type_list if w[-1] not in {"-", "+"}}
            same_word(client, message, "remove", word, word_type_list, mid)
        elif not word_type and not word and message.reply_to_message:
            r_message = message.reply_to_message
            aid = r_message.from_user.id

            # Check permission
            if uid != aid:
                return True

            old_command_list = list(filter(None, get_text(r_message).split()))
            old_command = old_command_list[0][1:]

            # Check old command's format
            if (len(old_command_list) > 2
                    and old_command in glovar.add_commands):
                word_type, word = get_command_context(r_message)
                word_type_list = get_same_types(word)
                word_type_list.discard(word_type)

                if f"{word_type}-" in word_type_list or f"{word_type}+" in word_type_list:
                    return True

                word_type_list = {w for w in word_type_list if w[-1] not in {"-", "+"}}
                same_word(client, r_message, "remove", word, word_type_list, mid)

        return True
    except Exception as e:
        logger.warning(f"Remove word error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["reset"], glovar.prefix)
                   & regex_group
                   & from_user)
def reset_words(client: Client, message: Message) -> bool:
    # Push words
    glovar.locks["regex"].acquire()
    try:
        # Basic data
        cid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{mention_id(uid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_reset'))}\n")

        # Proceed
        command_type = get_command_type(message)

        if command_type in glovar.regex:
            for word in list(eval(f"glovar.{command_type}_words")):
                eval(f"glovar.{command_type}_words")[word] = deepcopy(glovar.default_word_status)

            save(f"{command_type}_words")

            text += f"{lang('type')}{lang('colon')}{code(lang(command_type))}\n"

            if glovar.comments.get(command_type):
                text += f"{lang('comment')}{lang('colon')}{code(glovar.comments[command_type])}\n"

            text += f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
        elif command_type == "all":
            for word_type in glovar.regex:
                for word in list(eval(f"glovar.{word_type}_words")):
                    eval(f"glovar.{word_type}_words")[word] = deepcopy(glovar.default_word_status)

                save(f"{word_type}_words")

            text += (f"{lang('type')}{lang('colon')}{code(lang('all'))}\n"
                     f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n")
        else:
            text += (f"{lang('type')}{lang('colon')}{code(command_type or lang('unknown'))}\n"
                     f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Reset words error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(glovar.same_commands, glovar.prefix)
                   & regex_group & from_user)
def same_words(client: Client, message: Message) -> bool:
    # Same with other types
    glovar.locks["regex"].acquire()
    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id
        uid = message.from_user.id
        r_message = message.reply_to_message
        rid = r_message and r_message.message_id

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{mention_id(uid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_same'))}\n")

        # Get this new command's list
        command_type = get_command_type(message)
        new_word_type_list = set(command_type.split())

        # Check new command's format
        if (r_message
                and new_word_type_list
                and all(new_word_type in glovar.regex for new_word_type in new_word_type_list)):
            aid = r_message.from_user.id

            # Check permission
            if uid == aid:
                old_command_list = list(filter(None, get_text(r_message).split()))
                old_command = old_command_list[0][1:]

                # Check old command's format
                if (len(old_command_list) > 2
                        and old_command in glovar.add_commands + glovar.remove_commands):
                    _, old_word = get_command_context(r_message)
                    same_word(client, r_message, old_command, old_word, new_word_type_list, mid)
                    return True

                # If origin old message just simply "/rm", bot should check which message it replied to
                elif (old_command in glovar.remove_commands
                      and len(old_command_list) == 1):
                    # Get the message replied by r_message
                    r_message = get_message(client, cid, rid)

                    if r_message.reply_to_message:
                        r_message = r_message.reply_to_message
                        aid = r_message.from_user.id

                        # Check permission
                        if uid == aid:
                            old_command_list = list(filter(None, get_text(r_message).split()))
                            old_command = old_command_list[0][1:]

                            # Check old command's format
                            if (len(old_command_list) > 2
                                    and old_command in glovar.add_commands):
                                _, old_word = get_command_context(r_message)
                                same_word(client, r_message, "remove", old_word, new_word_type_list, mid)
                                return True
                            else:
                                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                                         f"{lang('reason')}{lang('colon')}{code(lang('command_reply'))}\n")
                        else:
                            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                                     f"{lang('reason')}{lang('colon')}{code(lang('command_permission'))}\n")
                    else:
                        text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                                 f"{lang('reason')}{lang('colon')}{code(lang('command_reply'))}\n")
                else:
                    text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                             f"{lang('reason')}{lang('colon')}{code(lang('command_reply'))}\n")
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('command_permission'))}\n")
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Same words error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(glovar.search_commands, glovar.prefix)
                   & regex_group
                   & from_user)
def search_words(client: Client, message: Message) -> bool:
    # Search words
    glovar.locks["regex"].acquire()
    try:
        # Basic data
        cid = message.chat.id
        mid = message.message_id

        # Send the report message
        text, markup = words_search(message, message.command[0])
        thread(send_message, (client, cid, text, mid, markup))

        return True
    except Exception as e:
        logger.warning(f"Search words error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["t2t"], glovar.prefix)
                   & test_group
                   & from_user)
def text_t2t(client: Client, message: Message) -> bool:
    # Transfer text
    glovar.locks["regex"].acquire()
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('t2t'))}\n")

        # Get command type
        command_type = get_command_type(message)

        if message.reply_to_message:
            # Regenerate special characters dictionary if possible
            for file_name in {"spc_words", "spe_words"}:
                special = file_name.split("_")[0]
                exec(f"glovar.{special}_dict = {{}}")

                for rule in list(eval(f"glovar.{file_name}")):
                    # Check keys
                    if "[" not in rule:
                        continue

                    # Check value
                    if "?#" not in rule:
                        continue

                    keys = rule.split("]")[0][1:]
                    value = rule.split("?#")[1][1]

                    for k in keys:
                        eval(f"glovar.{special}_dict")[k] = value

            result = ""

            forward_name = get_forward_name(message.reply_to_message, True, True)

            if forward_name:
                result += forward_name + "\n\n"

            file_name = get_filename(message.reply_to_message, True, True)

            if file_name:
                result += file_name + "\n\n"

            message_text = get_text(message.reply_to_message, True, True)

            if message_text:
                result += message_text + "\n\n"

            result = result.strip()

            if result and command_type == "pure":
                result = re.sub(r"""[^\da-zA-Z一-龥.,:'"?!~;()。，？！～@“”]""", "", result)

            if result:
                text += f"{lang('result')}{lang('colon')}" + "-" * 24 + "\n\n"
                text += code_block(result) + "\n"
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_none'))}\n")
        else:
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Text t2t error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["version"], glovar.prefix)
                   & test_group
                   & from_user)
def version(client: Client, message: Message) -> bool:
    # Check the program's version
    result = False

    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id

        # Get command type
        command_type = get_command_type(message)

        # Check the command type
        if command_type and command_type.upper() != glovar.sender:
            return False

        # Version info
        git_change = bool(run("git diff-index HEAD --", stdout=PIPE, shell=True).stdout.decode().strip())
        git_date = run("git log -1 --format='%at'", stdout=PIPE, shell=True).stdout.decode()
        git_date = get_readable_time(get_int(git_date), "%Y/%m/%d %H:%M:%S")
        git_hash = run("git rev-parse --short HEAD", stdout=PIPE, shell=True).stdout.decode()
        get_hash_link = f"https://github.com/scp-079/scp-079-{glovar.sender.lower()}/commit/{git_hash}"
        command_date = get_readable_time(message.date, "%Y/%m/%d %H:%M:%S")

        # Generate the text
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n\n"
                f"{lang('project')}{lang('colon')}{code(glovar.sender)}\n"
                f"{lang('version')}{lang('colon')}{code(glovar.version)}\n"
                f"{lang('本地修改')}{lang('colon')}{code(git_change)}\n"
                f"{lang('哈希值')}{lang('colon')}{general_link(git_hash, get_hash_link)}\n"
                f"{lang('提交时间')}{lang('colon')}{code(git_date)}\n"
                f"{lang('命令发送时间')}{lang('colon')}{code(command_date)}\n")

        # Send the report message
        result = send_message(client, cid, text, mid)
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)

    return result


@Client.on_message(Filters.incoming & Filters.group & Filters.command(["who"], glovar.prefix)
                   & regex_group
                   & from_user)
def who(client: Client, message: Message) -> bool:
    # Find who add the word
    glovar.locks["regex"].acquire()
    try:
        # Basic data
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id

        # Text prefix
        text = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('action_who'))}\n")

        # Proceed
        word_type, word = get_command_context(message)

        if word_type and word_type in glovar.regex and word:
            words = eval(f"glovar.{word_type}_words")

            text += f"{lang('type')}{lang('colon')}{code(lang(word_type))}\n"

            if glovar.comments.get(word_type):
                text += f"{lang('comment')}{lang('colon')}{code(glovar.comments[word_type])}\n"

            text += f"{lang('word')}{lang('colon')}{code(word)}\n"

            if word in words:
                uid = words[word].get("who", 0)
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_succeeded'))}\n"
                         f"{lang('result')}{lang('colon')}{code(uid)}\n")
            else:
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_not_exist'))}\n")
        else:
            text += (f"{lang('type')}{lang('colon')}{code(word_type or lang('unknown'))}\n"
                     f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('command_usage'))}\n")

        # Send the report message
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Who error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False

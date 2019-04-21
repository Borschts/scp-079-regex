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


from pyrogram import Filters

from .. import glovar


def is_creator(_, message):
    uid = message.from_user.id
    if uid == glovar.creator_id:
        return True

    return False


the_creator = Filters.create(
    name="The Creator",
    func=is_creator
)

the_channel = Filters.create(
    name="The Channel",
    func=lambda flt, callback_query: callback_query.data == b"Pyrogram"
)

the_group = Filters.create(
    name="The Group",
    func=lambda flt, callback_query: callback_query.data == b"Pyrogram"
)

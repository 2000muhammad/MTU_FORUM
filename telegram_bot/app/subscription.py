from telegram.constants import ChatMemberStatus
from .api import get_channels

ACTIVE_STATUSES = {ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}


async def missing_channels(bot, user_id):
    missing = []
    for channel in get_channels():
        try:
            member = await bot.get_chat_member(channel["telegram_chat_id"], user_id)
            if member.status not in ACTIVE_STATUSES:
                missing.append(channel)
        except Exception:
            missing.append(channel)
    return missing

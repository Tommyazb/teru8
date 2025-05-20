import discord
import re
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

TEXT_CHANNEL_ID = 1356252919002824899  
FORUM_CHANNEL_ID = 1351786368044371998  
FORUM_CHANNEL_DUPLICATE_ID = 1351790186580803584  # 再投稿先

@bot.event
async def on_ready():
    print(f"✅ ログイン完了: {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # ========== 🧵 スレッド作成処理 ==========
    if message.channel.id == TEXT_CHANNEL_ID:
        content = message.content

        if "invalid" in content.lower() or "continuing reroll" not in content.lower():
            return

        id_match = re.search(r"\[[^:\[\]]+:[^\[\]]+\]", content)
        if not id_match:
            await message.add_reaction("🟡")
            return

        card_match = re.search(r"\[[A-Za-z0-9]+\]", content)
        if card_match:
            card_name = card_match.group()
        elif "double two star" in content.lower():
            card_name = "Double two star"
        elif "god pack" in content.lower():
            card_name = "God pack"
        else:
            await message.add_reaction("🟡")
            return

        thread_title = f"{card_name} {id_match.group()}"

        image_attachments = []
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith("image/"):
                image_attachments.append(await attachment.to_file())
            if len(image_attachments) == 2:
                break

        forum_channel = bot.get_channel(FORUM_CHANNEL_ID)
        if not isinstance(forum_channel, discord.ForumChannel):
            await message.add_reaction("❌")
            return

        try:
            await forum_channel.create_thread(
                name=thread_title[:100],
                content=content,
                files=image_attachments if image_attachments else None
            )
            await message.add_reaction("✅")
        except Exception as e:
            await message.add_reaction("❌")
            await message.channel.send("ERROR")

    # ========== 🔁 Botへのリプライ処理（スレッド内） ==========
    elif isinstance(message.channel, discord.Thread):
        thread = message.channel
        parent_forum = thread.parent

        # Bot自身にメンションされているかチェック
        if bot.user in message.mentions and parent_forum and parent_forum.id == FORUM_CHANNEL_ID:
            try:
                # スレッド名を変更（⭕がついていなければ先頭に追加）
                if not thread.name.startswith("⭕"):
                    new_title = f"⭕{thread.name}"
                    await thread.edit(name=new_title)

                # 再投稿先のフォーラム
                duplicate_forum = bot.get_channel(FORUM_CHANNEL_DUPLICATE_ID)
                if not isinstance(duplicate_forum, discord.ForumChannel):
                    await message.add_reaction("❌")
                    return

                # 再投稿（本文・画像含む）
                image_attachments = []
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        image_attachments.append(await attachment.to_file())
                    if len(image_attachments) == 2:
                        break

                await duplicate_forum.create_thread(
                    name=thread.name[:100],
                    content=message.content,
                    files=image_attachments if image_attachments else None
                )

                await message.add_reaction("✅")

            except Exception as e:
                await message.add_reaction("❌")
                await message.channel.send("ERROR")

    await bot.process_commands(message)
# Bot起動
bot.run(TOKEN)
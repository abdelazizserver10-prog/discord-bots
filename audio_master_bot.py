import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio

# =========================================================
# ⚙️ إعدادات بوت الصوت - Audio Master
# =========================================================
import os
TOKEN = os.getenv('AUDIO_MASTER_TOKEN')
VCOD_CATEGORY_ID = 1449115786127085719
VCOD_CHANNEL_NAME = "اضغط للدخول ➕"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=['!', '-', '/'], intents=intents)

# تخزين البيانات
active_temp_channels = {}

# =========================================================
# 🎤 نظام القنوات الصوتية المؤقتة (Voice System)
# =========================================================

class VoiceControlView(View):
    def __init__(self, owner_id, channel):
        super().__init__(timeout=None)
        self.owner_id = owner_id
        self.channel = channel

    async def check_owner(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ هذا الروم ليس ملكك!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✏️ تغيير الاسم", style=discord.ButtonStyle.blurple, custom_id="vc_rename")
    async def rename_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): 
            return
        
        await interaction.response.send_message("👇 اكتب الاسم الجديد في الشات الآن (معاك 30 ثانية):", ephemeral=True)
        
        def check(m): 
            return m.author == interaction.user and m.channel == self.channel
        
        try:
            msg = await interaction.client.wait_for('message', check=check, timeout=30)
            await self.channel.edit(name=msg.content)
            await msg.delete() 
            await interaction.followup.send(f"✅ تم تغيير الاسم إلى: **{msg.content}**", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ انتهى الوقت.", ephemeral=True)

    @discord.ui.button(label="🔒 قفل/فتح", style=discord.ButtonStyle.gray, custom_id="vc_lock")
    async def lock_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): 
            return
        
        voice_channel = self.channel
        current_perms = voice_channel.overwrites_for(interaction.guild.default_role)
        
        if current_perms.connect is False:
            await voice_channel.set_permissions(interaction.guild.default_role, connect=True)
            button.label = "🔒 قفل"
            button.style = discord.ButtonStyle.gray
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("🔓 تم فتح الروم للجميع.", ephemeral=True)
        else:
            await voice_channel.set_permissions(interaction.guild.default_role, connect=False)
            button.label = "🔓 فتح"
            button.style = discord.ButtonStyle.red
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("🔒 تم قفل الروم.", ephemeral=True)

    @discord.ui.button(label="🚫 طرد عضو", style=discord.ButtonStyle.danger, custom_id="vc_kick")
    async def kick_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_owner(interaction): 
            return
        
        members = [m for m in self.channel.members if m.id != self.owner_id]
        if not members:
            return await interaction.response.send_message("👀 الروم فاضي (مفيش غيرك)!", ephemeral=True)
        
        kick_view = View()
        select = discord.ui.Select(placeholder="اختر عضو لطرده...", options=[
            discord.SelectOption(label=m.display_name, value=str(m.id)) for m in members[:25]
        ])
        
        async def kick_callback(inter):
            member_to_kick = inter.guild.get_member(int(select.values[0]))
            if member_to_kick:
                await member_to_kick.move_to(None) 
                await inter.response.send_message(f"👋 تم طرد {member_to_kick.display_name}", ephemeral=True)
            else:
                await inter.response.send_message("❌ العضو خرج بالفعل.", ephemeral=True)
        
        select.callback = kick_callback
        kick_view.add_item(select)
        await interaction.response.send_message("اختر العضو:", view=kick_view, ephemeral=True)

class TemporaryChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_to_create_name = VCOD_CHANNEL_NAME
        self.category_id = VCOD_CATEGORY_ID

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel and after.channel.name == self.channel_to_create_name:
            if member.id in active_temp_channels:
                existing_channel = self.bot.get_channel(active_temp_channels[member.id])
                if existing_channel:
                    await member.move_to(existing_channel)
                    return
                else:
                    del active_temp_channels[member.id]

            guild = member.guild
            category = guild.get_channel(self.category_id)
            
            if not category:
                category = discord.utils.get(guild.categories, id=self.category_id)

            channel_name = f"🎧 {member.display_name}"
            if member.activity and member.activity.type == discord.ActivityType.playing:
                channel_name = f"🎮 {member.activity.name}"

            new_channel = await guild.create_voice_channel(name=channel_name, category=category)
            
            active_temp_channels[member.id] = new_channel.id
            
            await member.move_to(new_channel)
            await new_channel.set_permissions(member, connect=True, manage_channels=True)

            embed = discord.Embed(
                title="⚙️ لوحة تحكم الروم",
                description=f"أهلاً بك **{member.display_name}** في رومك الخاص!\nاستخدم الأزرار بالأسفل للتحكم.",
                color=discord.Color.from_rgb(47, 49, 54)
            )
            embed.set_footer(text="سيتم حذف الروم تلقائياً عند المغادرة.")
            await new_channel.send(member.mention, embed=embed, view=VoiceControlView(member.id, new_channel))

        if before.channel and before.channel.id in active_temp_channels.values():
            if len(before.channel.members) == 0:
                owner_id = None
                for uid, cid in active_temp_channels.items():
                    if cid == before.channel.id:
                        owner_id = uid
                        break
                
                if owner_id: 
                    del active_temp_channels[owner_id]
                await before.channel.delete()

@bot.event
async def on_ready():
    print(f'✅ {bot.user} - Audio Master متصل بنجاح!')
    await bot.add_cog(TemporaryChannel(bot))
    print("✅ نظام القنوات الصوتية جاهز")

@bot.event
async def on_member_join(m):
    c = discord.utils.get(m.guild.text_channels, name="منورين🫶")
    if c: 
        await c.send(f"منور يا {m.mention} ❤️")

bot.run(TOKEN)

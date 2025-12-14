import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio

# =========================================================
# ⚙️ إعدادات بوت الإبلاغ - Report Shield
# =========================================================
import os
TOKEN = os.getenv('REPORT_SHIELD_TOKEN')
LOG_CHANNEL_ID = 1449044075041787904

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=['!', '-', '/'], intents=intents)

# تخزين البيانات
active_tickets = {}

# =========================================================
# 🚨 نظام الإبلاغ عن المشاكل (Report System)
# =========================================================

class ReportIssueView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚨 الإبلاغ عن مشكلة", style=discord.ButtonStyle.red, custom_id="report_issue", emoji="⚠️")
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        if user.id in active_tickets and bot.get_channel(active_tickets[user.id]):
            return await interaction.response.send_message("❌ لديك تذكرة مفتوحة بالفعل!", ephemeral=True)

        category = discord.utils.get(guild.categories, name="🚨 Reports")
        if not category:
            category = await guild.create_category("🚨 Reports")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True),
        }

        for role in guild.roles:
            if role.permissions.administrator or role.name.lower() == "owner":
                overwrites[role] = discord.PermissionOverwrite(read_messages=True)

        channel = await guild.create_text_channel(f"🚨-{user.name}", category=category, overwrites=overwrites)
        active_tickets[user.id] = channel.id

        report_embed = discord.Embed(
            title="🚨 تذكرة إبلاغ عن مشكلة",
            description=f"مرحباً {user.mention}!\n\nشكراً لإبلاغك عن المشكلة.\nيرجى وصف المشكلة بالتفصيل حتى نتمكن من مساعدتك بسرعة.\n\n📝 **معلومات التذكرة:**\n• التاريخ: <t:{int(discord.utils.utcnow().timestamp())}:F>\n• المبلِّغ: {user.mention}",
            color=discord.Color.red()
        )
        report_embed.add_field(name="🔐 الخصوصية", value="هذه التذكرة مرئية فقط لك والإداريين ومالك السيرفر", inline=False)
        report_embed.set_thumbnail(url=user.avatar)
        report_embed.set_footer(text="فريق الدعم سيصل قريباً ⏳")
        
        await channel.send(f"{user.mention}", embed=report_embed)
        await interaction.response.send_message(f"✅ تم فتح تذكرتك: {channel.mention}", ephemeral=True)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} - Report Shield متصل بنجاح!')
    bot.add_view(ReportIssueView())
    print("✅ نظام الإبلاغ جاهز")

@bot.command()
async def setup_reports(ctx):
    if ctx.author.guild_permissions.administrator:
        report_embed = discord.Embed(
            title="🚨 نظام الإبلاغ عن المشاكل الأسطوري",
            description="اضغط على الزر أدناه للإبلاغ عن أي مشكلة تواجهها\n\n📌 ملاحظة: التذكرة مرئية فقط لك والإداريين",
            color=discord.Color.red()
        )
        report_embed.set_footer(text="نحن هنا لمساعدتك ⚡")
        await ctx.send(embed=report_embed, view=ReportIssueView())

bot.run(TOKEN)

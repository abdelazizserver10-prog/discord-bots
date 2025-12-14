import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import random
from datetime import datetime, timedelta

# =========================================================
# ⚙️ إعدادات البوت
# =========================================================
import os
TOKEN = os.getenv('GIVEAWAY_MASTER_TOKEN')
GIVEAWAY_CHANNEL_ID = 1449405549803470992  # قناة الإدارة (للإعدادات فقط - مخفية عن العضويسين)
GIVEAWAY_ANNOUNCEMENTS_CHANNEL_ID = 1449406615496294431  # قناة إعلان السحب للجميع
ADMIN_ROLE_ID = 1449002208963334184  # رتبة الإدارة

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=['!', '-', '/'], intents=intents)

# تخزين بيانات القرعات النشطة
active_giveaways = {}

# =========================================================
# 🎁 نظام السحب (Giveaway System)
# =========================================================

class GiveawayParticipantView(View):
    """زر المشاركة في السحب"""
    def __init__(self, giveaway_id):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id

    @discord.ui.button(label="🎁 اشترك بالسحب", style=discord.ButtonStyle.success, custom_id="join_giveaway", emoji="✨")
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        giveaway = active_giveaways.get(self.giveaway_id)
        if not giveaway:
            return await interaction.response.send_message("❌ السحب غير موجودة!", ephemeral=True)

        # التحقق من انتهاء السحب
        if giveaway['end_time'] < datetime.utcnow():
            return await interaction.response.send_message("⏰ انتهت السحب للأسف!", ephemeral=True)

        # التحقق من عدم اشتراك المستخدم مسبقاً
        if interaction.user.id in giveaway['participants']:
            return await interaction.response.send_message("✅ أنت مشترك بالفعل في السحب!", ephemeral=True)

        # إضافة المستخدم
        giveaway['participants'].add(interaction.user.id)
        
        join_embed = discord.Embed(
            title="✅ تمت الإضافة بنجاح!",
            description=f"تم إضافتك للسحب بنجاح! 🎉\n\nعدد المشاركين حالياً: **{len(giveaway['participants'])}**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=join_embed, ephemeral=True)
        
        # تحديث رسالة السحب
        await update_giveaway_message(giveaway)


async def update_giveaway_message(giveaway):
    """تحديث رسالة السحب لإظهار عدد المشاركين"""
    try:
        channel = bot.get_channel(giveaway['channel_id'])
        message = await channel.fetch_message(giveaway['message_id'])
        
        time_left = (giveaway['end_time'] - datetime.utcnow()).total_seconds()
        minutes_left = int(time_left // 60)
        seconds_left = int(time_left % 60)
        
        embed = discord.Embed(
            title="🎁 سحب أسطورية 🎁",
            description=f"**الجائزة:** {giveaway['prize']}\n\n" +
                       f"**الوقت المتبقي:** {minutes_left:02d}:{seconds_left:02d}\n" +
                       f"**عدد المشاركين:** {len(giveaway['participants'])} 👥\n\n" +
                       f"اضغط على الزر أدناه للاشتراك!",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"ستنتهي السحب في: {giveaway['end_time'].strftime('%H:%M:%S')}")
        
        await message.edit(embed=embed, view=GiveawayParticipantView(giveaway['giveaway_id']))
    except:
        pass


class GiveawaySetupView(View):
    """واجهة إعداد السحب (للإدارة فقط)"""
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.prize = None
        self.duration = None

    @discord.ui.button(label="🎯 إعداد سحب جديدة", style=discord.ButtonStyle.blurple, custom_id="setup_giveaway")
    async def setup_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ فقط الإدارة!", ephemeral=True)

        # طلب الجائزة
        await interaction.response.send_message(
            "📝 **اكتب الجائزة** (اسم الجائزة) في الشات في غضون 60 ثانية:",
            ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await bot.wait_for('message', check=check, timeout=60)
            self.prize = msg.content
            await msg.delete()
        except asyncio.TimeoutError:
            return await interaction.followup.send("⏰ انتهى الوقت!", ephemeral=True)

        # طلب المدة الزمنية
        await interaction.followup.send(
            "⏱️ **اكتب مدة السحب بالدقائق** (مثلاً: 5 أو 10 أو 30) في الشات:",
            ephemeral=True
        )

        try:
            msg = await bot.wait_for('message', check=check, timeout=60)
            self.duration = int(msg.content)
            await msg.delete()
        except (asyncio.TimeoutError, ValueError):
            return await interaction.followup.send("⏰ أدخل رقماً صحيحاً!", ephemeral=True)

        # إنشاء السحب
        await create_giveaway(interaction, self.prize, self.duration)


async def create_giveaway(interaction, prize, duration_minutes):
    """إنشاء السحب والإعلان عنها"""
    # إنشاء معرف فريد للسحب
    giveaway_id = f"gw_{interaction.guild.id}_{int(datetime.utcnow().timestamp())}"
    
    # حساب وقت الانتهاء
    end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    # البيانات الأساسية للسحب
    giveaway_data = {
        'giveaway_id': giveaway_id,
        'prize': prize,
        'host': interaction.user,
        'duration': duration_minutes,
        'start_time': datetime.utcnow(),
        'end_time': end_time,
        'participants': set(),
        'channel_id': GIVEAWAY_ANNOUNCEMENTS_CHANNEL_ID,
        'message_id': None,
        'finished': False
    }
    
    # الإعلان عن السحب
    channel = bot.get_channel(GIVEAWAY_ANNOUNCEMENTS_CHANNEL_ID)
    
    announcement_embed = discord.Embed(
        title="🎁✨ سحب أسطورية جديدة ✨🎁",
        description=f"**الجائزة:** {prize}\n\n" +
                   f"**مدة السحب:** {duration_minutes} دقيقة\n" +
                   f"**المضيف:** {interaction.user.mention}\n\n" +
                   f"اضغط على الزر أدناه للاشتراك الآن!",
        color=discord.Color.from_rgb(255, 215, 0)
    )
    announcement_embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1995/1995515.png")
    announcement_embed.set_footer(text=f"ستنتهي السحب في: {end_time.strftime('%H:%M:%S')}")
    
    giveaway_msg = await channel.send(embed=announcement_embed, view=GiveawayParticipantView(giveaway_id))
    giveaway_data['message_id'] = giveaway_msg.id
    
    # حفظ بيانات السحب
    active_giveaways[giveaway_id] = giveaway_data
    
    # إرسال تأكيد للإدارة
    confirm_embed = discord.Embed(
        title="✅ تم إنشاء السحب بنجاح!",
        description=f"**الجائزة:** {prize}\n**المدة:** {duration_minutes} دقيقة\n\nسيتم اختيار الفائز تلقائياً عند انتهاء الوقت!",
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=confirm_embed, ephemeral=True)
    
    # بدء العد العكسي
    await countdown_giveaway(giveaway_id)


async def countdown_giveaway(giveaway_id):
    """العد العكسي لانتهاء السحب واختيار الفائز"""
    giveaway = active_giveaways[giveaway_id]
    
    while datetime.utcnow() < giveaway['end_time'] and not giveaway['finished']:
        await asyncio.sleep(5)  # تحديث كل 5 ثواني
        await update_giveaway_message(giveaway)
    
    # انتهاء السحب - اختيار الفائز
    giveaway['finished'] = True
    
    if not giveaway['participants']:
        # لا يوجد مشاركين
        channel = bot.get_channel(giveaway['channel_id'])
        no_participants_embed = discord.Embed(
            title="❌ لا يوجد مشاركين في السحب!",
            description="لم يشترك أحد في السحب للأسف 😢",
            color=discord.Color.red()
        )
        await channel.send(embed=no_participants_embed)
        del active_giveaways[giveaway_id]
        return
    
    # اختيار فائز عشوائي
    winner_id = random.choice(list(giveaway['participants']))
    winner = bot.get_user(winner_id)
    
    if not winner:
        winner = await bot.fetch_user(winner_id)
    
    # إعلان الفائز
    channel = bot.get_channel(giveaway['channel_id'])
    
    winner_embed = discord.Embed(
        title="🎉🎁 تم اختيار الفائز! 🎁🎉",
        description=f"**مبروك يا {winner.mention}!**\n\n" +
                   f"**الجائزة:** {giveaway['prize']}\n\n" +
                   f"سيتواصل معك أحد الإدارة قريباً في الخاص! 📬\n\n" +
                   f"عدد المشاركين: {len(giveaway['participants'])}",
        color=discord.Color.gold()
    )
    winner_embed.set_thumbnail(url=winner.avatar)
    winner_embed.set_footer(text="شكراً لمشاركتك!")
    
    announcement = await channel.send(winner.mention, embed=winner_embed)
    
    # إرسال رسالة خاصة للفائز
    try:
        dm_embed = discord.Embed(
            title="🎁 مبروك! أنت الفائز! 🎁",
            description=f"تهانينا! لقد فزت في السحب!\n\n" +
                       f"**الجائزة:** {giveaway['prize']}\n\n" +
                       f"سيتواصل معك أحد الإدارة قريباً للتأكيد والتفاصيل.",
            color=discord.Color.gold()
        )
        dm_embed.set_footer(text="شكراً على مشاركتك!")
        await winner.send(embed=dm_embed)
    except:
        pass
    
    # حذف البيانات
    del active_giveaways[giveaway_id]


@bot.command(name="create_giveaway", aliases=['cg', 'giveaway'])
async def create_giveaway_cmd(ctx):
    """أمر إنشاء سحب جديدة (للإدارة فقط)"""
    if not ctx.author.guild_permissions.administrator:
        admin_embed = discord.Embed(
            title="❌ صلاحية مطلوبة",
            description="فقط الإدارة يمكنها إنشاء قرعات!",
            color=discord.Color.red()
        )
        return await ctx.send(embed=admin_embed)
    
    setup_embed = discord.Embed(
        title="⚙️ إعداد السحب",
        description="اضغط على الزر أدناه لإنشاء سحب جديدة",
        color=discord.Color.blurple()
    )
    
    await ctx.send(embed=setup_embed, view=GiveawaySetupView(ctx))


@bot.event
async def on_ready():
    print(f'✅ Giveaway Master متصل: {bot.user}')
    print("✨ نظام السحب الأسطوري جاهز!")

bot.run(TOKEN)

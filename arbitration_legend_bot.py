import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio

# =========================================================
# ⚙️ إعدادات بوت الوساطة - Arbitration Legend
# =========================================================
import os
TOKEN = os.getenv('ARBITRATION_LEGEND_TOKEN')
MIDDLEMAN_ROLE_ID = 1449002208963334184
LOG_CHANNEL_ID = 1449044075041787904

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=['!', '-', '/'], intents=intents)

# تخزين البيانات
active_tickets = {}

# =========================================================
# 🎟️ نظام الوساطة (Arbitration System)
# =========================================================

class CloseOptionView(View):
    def __init__(self): 
        super().__init__(timeout=None)
    
    @discord.ui.button(label="✅ تمت العملية", style=discord.ButtonStyle.green, custom_id="c_success")
    async def s(self, i, b):
        await i.response.defer()
        m, c = i.user, i.channel
        for p in [x for x in c.members if not x.bot and x != m]:
            try:
                rating_embed = discord.Embed(
                    title="⭐ تقييم الوسيط الأسطوري",
                    description=f"ما رأيك في خدمات {m.mention}؟\n\nاختر التقييم المناسب من الأزرار أدناه",
                    color=discord.Color.from_rgb(255, 215, 0)
                )
                rating_embed.set_thumbnail(url=m.avatar)
                rating_embed.set_footer(text="تقييمك مهم جداً لنا")
                await p.send(embed=rating_embed, view=EnhancedRatingView(m, p))
            except: pass
        
        completion_embed = discord.Embed(
            title="🎉 تمت العملية بنجاح",
            description="سيتم حذف التذكرة خلال 5 ثواني...",
            color=discord.Color.green()
        )
        await c.send(embed=completion_embed)
        await asyncio.sleep(5)
        if m.id in active_tickets: del active_tickets[m.id]
        await c.delete()
    
    @discord.ui.button(label="❌ إلغاء", style=discord.ButtonStyle.red, custom_id="c_fail")
    async def f(self, i, b):
        cancel_embed = discord.Embed(
            title="❌ تم إلغاء التذكرة",
            description="سيتم حذف التذكرة خلال 3 ثواني...",
            color=discord.Color.red()
        )
        await i.response.send_message(embed=cancel_embed)
        await asyncio.sleep(3)
        if i.user.id in active_tickets: del active_tickets[i.user.id]
        await i.channel.delete()

class TicketView(View):
    def __init__(self): 
        super().__init__(timeout=None)
    
    @discord.ui.button(label="⚖️ طلب وسيط", style=discord.ButtonStyle.blurple, custom_id="req_ticket", emoji="⚖️")
    async def c(self, i, b):
        if i.user.id in active_tickets and bot.get_channel(active_tickets[i.user.id]): 
            return await i.response.send_message("❌ لديك تذكرة مفتوحة بالفعل!", ephemeral=True)
        
        g = i.guild
        cat = discord.utils.get(g.categories, name="⚖️ Tickets") or await g.create_category("⚖️ Tickets")
        overwrites = {
            g.default_role: discord.PermissionOverwrite(read_messages=False), 
            i.user: discord.PermissionOverwrite(read_messages=True), 
            g.me: discord.PermissionOverwrite(read_messages=True)
        }
        r = g.get_role(MIDDLEMAN_ROLE_ID)
        if r: 
            overwrites[r] = discord.PermissionOverwrite(read_messages=True)
        
        ch = await g.create_text_channel(f"⚖️-{i.user.name}", category=cat, overwrites=overwrites)
        active_tickets[i.user.id] = ch.id
        
        # رسالة ترحيب ملحمية
        welcome_embed = discord.Embed(
            title="⚖️ تذكرة وساطة جديدة",
            description=f"مرحباً {i.user.mention}!\n\nأنت الآن في قناة الوساطة الخاصة بك.\nحدد اسم الوسيط الذي تريده أو انتظر أحدهم.",
            color=discord.Color.from_rgb(138, 43, 226)
        )
        welcome_embed.set_footer(text="استخدم الأزرار أدناه للتحكم في التذكرة", icon_url=i.user.avatar)
        
        await ch.send(f"{i.user.mention}", embed=welcome_embed, view=ControlView())
        await i.response.send_message(f"✅ تم فتح تذكرتك: {ch.mention}", ephemeral=True)

class ControlView(View):
    def __init__(self): 
        super().__init__(timeout=None)
    
    @discord.ui.button(label="➕ إضافة عضو", style=discord.ButtonStyle.success, custom_id="add_usr")
    async def a(self, i: discord.Interaction, b: discord.ui.Button):
        await i.response.send_message("👇 **منشن الشخص** اللي عايز تضيفه في الشات (معاك 60 ثانية):", ephemeral=True)
        
        def check(m):
            return m.author == i.user and m.channel == i.channel and len(m.mentions) > 0

        try:
            msg = await i.client.wait_for('message', check=check, timeout=60)
            member = msg.mentions[0]
            
            await i.channel.set_permissions(member, view_channel=True, send_messages=True, read_message_history=True)
            
            success_embed = discord.Embed(
                title="✅ تمت الإضافة بنجاح",
                description=f"تم إضافة {member.mention} للتذكرة",
                color=discord.Color.green()
            )
            await i.channel.send(embed=success_embed)
        
        except asyncio.TimeoutError:
            await i.followup.send("⏰ انتهى الوقت! اضغط الزر مرة تانية.", ephemeral=True)
        
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ حدث خطأ",
                description=f"الخطأ: {str(e)}",
                color=discord.Color.red()
            )
            await i.channel.send(embed=error_embed)

    @discord.ui.button(label="🔖 إنهاء التذكرة", style=discord.ButtonStyle.red, custom_id="cls_tkt")
    async def c(self, i, b):
        close_embed = discord.Embed(
            title="🔍 هل اكتملت المشكلة؟",
            description="اختر إذا تمت العملية أم لا",
            color=discord.Color.orange()
        )
        await i.response.send_message(embed=close_embed, view=CloseOptionView())

class EnhancedRatingView(View):
    def __init__(self, mediator, reporter):
        super().__init__(timeout=None)
        self.mediator = mediator
        self.reporter = reporter

    async def submit_rating(self, interaction, stars, star_count):
        prompt_embed = discord.Embed(
            title="✍️ أضف تعليقك (اختياري)",
            description="اكتب تعليقك في الشات. لديك 60 ثانية\n(إذا لم تكتب شيء سيتم تسجيل التقييم بدون تعليق)",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=prompt_embed, ephemeral=True)

        def check(m):
            return m.author == self.reporter and m.channel == interaction.channel

        try:
            msg = await bot.wait_for('message', check=check, timeout=60)
            comment = msg.content
            await msg.delete()
        except asyncio.TimeoutError:
            comment = "(لا يوجد تعليق)"

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="🌟 تقييم أسطوري جديد 🌟",
                color=discord.Color.from_rgb(255, 215, 0)
            )
            embed.set_thumbnail(url=self.mediator.avatar)
            
            stars_display = "⭐" * star_count + "☆" * (5 - star_count)
            
            embed.add_field(name="👤 الوسيط", value=self.mediator.mention, inline=True)
            embed.add_field(name="👤 من", value=self.reporter.mention, inline=True)
            embed.add_field(name="⭐ التقييم", value=f"{stars_display}\n({star_count}/5)", inline=True)
            embed.add_field(name="💬 التعليق", value=f">>> {comment}", inline=False)
            
            embed.set_footer(text=f"تم التقييم في {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
            
            await log_channel.send(embed=embed)

        thanks_embed = discord.Embed(
            title="✅ شكراً على تقييمك!",
            description="تقييمك مهم جداً ويساعدنا على تحسين الخدمة",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=thanks_embed, ephemeral=True)

    @discord.ui.button(label="⭐⭐⭐⭐⭐ ممتاز جداً", style=discord.ButtonStyle.success)
    async def rate_5(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, "⭐⭐⭐⭐⭐", 5)

    @discord.ui.button(label="⭐⭐⭐⭐ جيد جداً", style=discord.ButtonStyle.blurple)
    async def rate_4(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, "⭐⭐⭐⭐", 4)

    @discord.ui.button(label="⭐⭐⭐ جيد", style=discord.ButtonStyle.blurple)
    async def rate_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, "⭐⭐⭐", 3)

    @discord.ui.button(label="⭐⭐ مقبول", style=discord.ButtonStyle.gray)
    async def rate_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, "⭐⭐", 2)

    @discord.ui.button(label="⭐ سيء", style=discord.ButtonStyle.danger)
    async def rate_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_rating(interaction, "⭐", 1)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} - Arbitration Legend متصل بنجاح!')
    bot.add_view(TicketView())
    bot.add_view(ControlView())
    bot.add_view(CloseOptionView())
    print("✅ جميع أنظمة الوساطة جاهزة")

@bot.command()
async def setup(ctx):
    if ctx.author.guild_permissions.administrator:
        setup_embed = discord.Embed(
            title="⚖️ نظام طلب الوسيط الأسطوري",
            description="اضغط على الزر أدناه لطلب وسيط موثوق لحل نزاعاتك",
            color=discord.Color.from_rgb(138, 43, 226)
        )
        setup_embed.set_footer(text="نحن هنا لمساعدتك 💫")
        await ctx.send(embed=setup_embed, view=TicketView())

bot.run(TOKEN)

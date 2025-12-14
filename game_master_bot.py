import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import random

# =========================================================
# ⚙️ إعدادات بوت الألعاب - Game Master
# =========================================================
import os
TOKEN = os.getenv('GAME_MASTER_TOKEN')
GAME_CHANNEL_NAME = "اوامر⏮️"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=['!', '-', '/'], intents=intents)

# =========================================================
# 🎮 نظام الألعاب (Games System)
# =========================================================

# --- لعبة البحث عن الكنز ---
class TreasureView(View):
    def __init__(self, author):
        super().__init__(timeout=20)
        self.author = author
        self.treasure_loc = random.randint(0, 4)
        for i in range(5):
            self.add_item(TreasureButton(i))

class TreasureButton(discord.ui.Button):
    def __init__(self, index):
        super().__init__(style=discord.ButtonStyle.secondary, label="📦", custom_id=f"box_{index}")
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view: TreasureView = self.view
        if interaction.user != view.author:
            return await interaction.response.send_message("مش لعبتك! ✋", ephemeral=True)

        if self.index == view.treasure_loc:
            self.style = discord.ButtonStyle.success
            self.label = "💎"
            self.emoji = None
            msg = "🎉 مبروووك! لقيت الكنز!"
            for item in view.children: 
                item.disabled = True
            await interaction.response.edit_message(content=msg, view=view)
            view.stop()
        else:
            self.style = discord.ButtonStyle.danger
            self.label = "🕸️"
            self.disabled = True
            await interaction.response.edit_message(content="صندوق فاضي! 😢 حاول تاني.", view=view)

@bot.command(name="find")
async def treasure_game(ctx):
    if ctx.channel.name != GAME_CHANNEL_NAME: 
        return await ctx.send(f"⚠️ العب في {GAME_CHANNEL_NAME}")
    await ctx.send("🏴‍☠️ **أين الكنز؟**\nواحد بس من الصناديق فيه ألماس 💎 والباقي عناكب 🕸️!", view=TreasureView(ctx.author))

# --- لعبة XO الذكية ---
class TicTacToeButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view.current_player == view.X:
            if interaction.user != view.player_user: 
                return await interaction.response.send_message("انتظر دورك!", ephemeral=True)
            
            view.board[self.y][self.x] = view.X
            self.style = discord.ButtonStyle.primary
            self.label = "❌"
            self.disabled = True
            
            winner = view.check_winner()
            if winner:
                await view.end_game(interaction, winner)
                return

            view.current_player = view.O
            await interaction.response.edit_message(content="🤖 البوت يفكر...", view=view)
            
            await asyncio.sleep(0.7)
            await view.bot_move(interaction)

class TicTacToeView(View):
    X = -1
    O = 1
    
    def __init__(self, player_user):
        super().__init__(timeout=60)
        self.player_user = player_user
        self.current_player = self.X
        self.board = [[0,0,0],[0,0,0],[0,0,0]]
        for y in range(3):
            for x in range(3): 
                self.add_item(TicTacToeButton(x, y))

    def check_winner(self):
        b = self.board
        lines = (
            b[0], b[1], b[2],
            [b[0][0], b[1][0], b[2][0]], [b[0][1], b[1][1], b[2][1]], [b[0][2], b[1][2], b[2][2]],
            [b[0][0], b[1][1], b[2][2]], [b[0][2], b[1][1], b[2][0]]
        )
        for line in lines:
            if line[0] == line[1] == line[2] != 0: 
                return line[0]
        if all(c!=0 for r in b for c in r): 
            return 2
        return None

    async def bot_move(self, interaction):
        move = self.find_winning_move(self.O)
        if not move: 
            move = self.find_winning_move(self.X)
        
        if not move:
            available = [child for child in self.children if not child.disabled]
            if available: 
                move = random.choice(available)
        
        if move:
            move.style = discord.ButtonStyle.danger
            move.label = "⭕"
            move.disabled = True
            self.board[move.y][move.x] = self.O
            self.current_player = self.X
            
            winner = self.check_winner()
            if winner:
                await interaction.message.edit(content=self.get_end_msg(winner), view=self)
                self.stop()
            else:
                await interaction.message.edit(content=f"🎮 دورك يا {self.player_user.mention} (❌)", view=self)

    def find_winning_move(self, player_val):
        for child in self.children:
            if not child.disabled:
                self.board[child.y][child.x] = player_val
                if self.check_winner() == player_val:
                    self.board[child.y][child.x] = 0
                    return child
                self.board[child.y][child.x] = 0
        return None

    async def end_game(self, interaction, winner):
        msg = self.get_end_msg(winner)
        for c in self.children: 
            c.disabled = True
        await interaction.response.edit_message(content=msg, view=self)
        self.stop()

    def get_end_msg(self, winner):
        if winner == self.X: 
            return f"👑 كفووو! {self.player_user.mention} جلد البوت!"
        elif winner == self.O: 
            return "🤖 البوت فاز! (ذكاء اصطناعي 😉)"
        else: 
            return "🤝 تعادل! جيم قوي."

@bot.command(name="xo")
async def xo_game(ctx):
    if ctx.channel.name != GAME_CHANNEL_NAME: 
        return await ctx.send(f"⚠️ العب في {GAME_CHANNEL_NAME}")
    await ctx.send(f"⚔️ **تحدي العمالقة**\n{ctx.author.mention} (❌) ضد البوت (⭕)", view=TicTacToeView(ctx.author))

# --- ماكينة الحظ ---
@bot.command(name="slots", aliases=['spin'])
async def slots_game(ctx):
    if ctx.channel.name != GAME_CHANNEL_NAME: 
        return await ctx.send(f"⚠️ العب في {GAME_CHANNEL_NAME}")
    
    emojis = ["🍇", "🍊", "🍒", "🔔", "💎", "7️⃣"]
    msg = await ctx.send(embed=discord.Embed(title="🎰 جاري اللف...", color=discord.Color.dark_magenta()))
    
    for _ in range(3):
        row = f"| {random.choice(emojis)} | {random.choice(emojis)} | {random.choice(emojis)} |"
        await msg.edit(embed=discord.Embed(title="🎰 Spinning...", description=f"**{row}**", color=discord.Color.purple()))
        await asyncio.sleep(0.4)
    
    r = [random.choice(emojis) for _ in range(3)]
    
    if r[0] == r[1] == r[2]:
        color = discord.Color.gold()
        title = "🔥🔥 JACKPOT 🔥🔥"
        desc = "ألف مبروك! لقد ربحت الجائزة الكبرى!"
    elif r[0] == r[1] or r[1] == r[2] or r[0] == r[2]:
        color = discord.Color.green()
        title = "✅ فوز صغير"
        desc = "جبت اثنين زي بعض، مش بطال!"
    else:
        color = discord.Color.red()
        title = "❌ حظ أوفر"
        desc = "جرب تاني يا بطل!"

    final_row = f"| {r[0]} | {r[1]} | {r[2]} |"
    await msg.edit(embed=discord.Embed(title=title, description=f"# {final_row}\n{desc}", color=color))

# --- حجرة ورقة مقص ---
class RPSView(View):
    def __init__(self, p): 
        super().__init__(timeout=30)
        self.p = p
    
    async def play(self, i, c):
        if i.user != self.p: 
            return await i.response.send_message("مش دورك!", ephemeral=True)
        bot_c = random.choice(["🪨", "📄", "✂️"])
        win = False
        if (c=="🪨" and bot_c=="✂️") or (c=="📄" and bot_c=="🪨") or (c=="✂️" and bot_c=="📄"): 
            win = True
        elif c == bot_c: 
            res = "تعادل 🤝"
            color = discord.Color.gold()
        else: 
            res = "البوت فاز 🤖"
            color = discord.Color.red()
        if win: 
            res = "أنت فزت 🎉"
            color = discord.Color.green()
        
        embed = discord.Embed(title=res, color=color)
        embed.add_field(name="أنت", value=c)
        embed.add_field(name="البوت", value=bot_c)
        await i.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="🪨", style=discord.ButtonStyle.primary)
    async def r(self, i, b): 
        await self.play(i, "🪨")
    
    @discord.ui.button(label="📄", style=discord.ButtonStyle.primary)
    async def p(self, i, b): 
        await self.play(i, "📄")
    
    @discord.ui.button(label="✂️", style=discord.ButtonStyle.primary)
    async def s(self, i, b): 
        await self.play(i, "✂️")

@bot.command(name="rps")
async def rps(ctx):
    if ctx.channel.name != GAME_CHANNEL_NAME: 
        return await ctx.send(f"⚠️ العب في {GAME_CHANNEL_NAME}")
    await ctx.send(embed=discord.Embed(title="RPS Game", description="اختار سلاحك!", color=discord.Color.blue()), view=RPSView(ctx.author))

@bot.event
async def on_ready():
    print(f'✅ {bot.user} - Game Master متصل بنجاح!')
    print("✅ جميع الألعاب جاهزة")

bot.run(TOKEN)

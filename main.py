import discord
from discord.ext import commands
from discord.ui import Button, View, Select

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

# Store server-wise settings (Guild ID -> Staff Role ID)
ticket_settings = {}

TICKET_CATEGORY_NAME = "🎫 • WHISPER TICKETS"

class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        guild_id = interaction.guild.id
        staff_role_id = ticket_settings.get(guild_id)
        
        is_staff = False
        if staff_role_id:
            role = interaction.guild.get_role(staff_role_id)
            if role and role in interaction.user.roles:
                is_staff = True

        if not is_staff and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Only Staff or Owner can close tickets!", ephemeral=True)
        
        await interaction.response.send_message("🔒 Ticket is deleting in 3 seconds...")
        await interaction.channel.delete()

    @discord.ui.button(label="🙋‍♂️ Claim Ticket", style=discord.ButtonStyle.primary, custom_id="claim_ticket")
    async def claim_ticket(self, interaction: discord.Interaction, button: Button):
        guild_id = interaction.guild.id
        staff_role_id = ticket_settings.get(guild_id)
        
        is_staff = False
        if staff_role_id:
            role = interaction.guild.get_role(staff_role_id)
            if role and role in interaction.user.roles:
                is_staff = True

        if not is_staff and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Only Staff can claim tickets!", ephemeral=True)
        
        button.disabled = True
        button.label = f"Claimed by {interaction.user.name}"
        button.style = discord.ButtonStyle.success
        await interaction.message.edit(view=self)
        await interaction.response.send_message(f"✅ This ticket has been claimed by **{interaction.user.mention}**!")

class TicketSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", description="For general questions or server help", emoji="💬"),
            discord.SelectOption(label="Bug Report", description="To report any glitches or bugs", emoji="🐛"),
            discord.SelectOption(label="Billing / Payments", description="For paid services or transactions", emoji="💳")
        ]
        super().__init__(placeholder="🎫 Select a category to open a ticket...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        guild_id = guild.id
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        
        if not category:
            category = await guild.create_category(TICKET_CATEGORY_NAME)

        # Permissions: Only user, bot, and the server's designated staff role can view
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        staff_role_id = ticket_settings.get(guild_id)
        mention_text = ""
        if staff_role_id:
            staff_role = guild.get_role(staff_role_id)
            if staff_role:
                overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                mention_text = staff_role.mention

        # Create a new ticket channel
        channel_name = f"ticket-{interaction.user.name}-{self.values[0].lower()[:5]}"
        ticket_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        
        embed = discord.Embed(
            title=f"Support Ticket: {self.values[0]}",
            description=f"Welcome {interaction.user.mention}!\nStaff will assist you shortly.\n\nUse the buttons below to manage your ticket.",
            color=discord.Color.from_rgb(138, 180, 248)
        )
        embed.set_footer(text="Whisper Ticket • Secure Support System")
        
        await ticket_channel.send(content=f"{interaction.user.mention} {mention_text}", embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ Your private ticket has been created: {ticket_channel.mention}", ephemeral=True)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# 1. Dynamic Ticket Setup Command
@bot.command(name="setticket")
@commands.has_permissions(administrator=True)
async def setticket(ctx, role: discord.Role = None):
    """Usage: !setticket @StaffRole"""
    if not role:
        return await ctx.send("❌ Please mention a staff role! Example: `!setticket @Staff`", delete_after=10)
    
    # Save the role for this specific server
    ticket_settings[ctx.guild.id] = role.id

    embed = discord.Embed(
        title="🌙 Whisper Ticket Support",
        description=f"Select a category from the dropdown menu below to open a private ticket for any assistance, bug reports, or payments!\n\n📌 **Staff Role:** {role.mention}",
        color=discord.Embed.Empty
    )
    embed.set_footer(text="Crafted with ❤️ by ADX Ankit")
    await ctx.send(embed=embed, view=TicketView())
    try:
        await ctx.message.delete()
    except:
        pass

# 2. Ping Command
@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Whisper Ticket is online and running smooth!\n⚡ Latency: **{latency}ms**",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# 3. Server Info Command
@bot.command(name="serverinfo")
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(
        title=f"📊 {guild.name} - Server Info",
        color=discord.Color.blue()
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="👑 Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
    embed.add_field(name="📅 Created On", value=guild.created_at.strftime("%b %d, %Y"), inline=False)
    await ctx.send(embed=embed)

# 4. Standard Help Command
@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="✨ Whisper Ticket Help Menu",
        description="Here is the list of all available bot commands:",
        color=discord.Color.purple()
    )
    embed.add_field(name="`!setticket @Role`", value="Sets the server's staff role and generates the ticket panel.", inline=False)
    embed.add_field(name="`!ping`", value="Checks the bot's response speed/latency.", inline=False)
    embed.add_field(name="`!serverinfo`", value="Displays details of the current server.", inline=False)
    embed.add_field(name="`!help`", value="Shows the list of all bot commands.", inline=False)
    embed.set_footer(text="Developed by ADX Ankit")
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} successfully!')
    activity = discord.Game(name="Whispering sweet solutions 💌")
    await bot.change_presence(activity=activity)

bot.run('YOUR_BOT_TOKEN')
                       

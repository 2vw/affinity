import discord, pymongo, motor, json, time, os
from discord.ext import commands
from motor import motor_asyncio

config = json.load(open("config.json"))

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

client = motor.motor_asyncio.AsyncIOMotorClient(f"mongodb+srv://admin:{config['DBPassword']}@cluster0.bc1nq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["affinityDB"]

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded {filename}")
            except Exception as e:
                print(f"Failed to load {filename}: {e}")
    await bot.sync_commands()

class register(discord.ui.View):
    @discord.ui.button(label="Accept", style=discord.ButtonStyle.danger)
    async def button_callback(self, button, interaction):
        db.users.insert_one(
            {
                "_id": interaction.user.id, 
                "blacklist": [], 
                "whitelist": [], 
                "banned": False, 
                "bantime": time.time(),
                "economy": {
                    "balance": 1500,
                    "gambling": {
                        "wins": 0,
                        "losses": 0,
                        "biggest_win": 0,
                        "biggest_loss": 0,
                        "total_wagered": 0,
                        "profit": 0
                    },
                "loans": {
                        "bank": {
                            "active": False,
                            "amount": 50000,
                            "interest": 0.05,
                            "per": 500,
                            "multiplier": 1,
                            "owed": 0
                        },
                        "school": {
                            "active": False,
                            "amount": 25000,
                            "interest": 0.05,
                            "per": 1000,
                            "multiplier": 1,
                            "owed": 0
                        },
                        "mafia": {
                            "active": False,
                            "amount": 500000,
                            "interest": 0.5,
                            "per": 1800,
                            "multiplier": 1,
                            "owed": 0
                        }
                        },
                        "total": 0,
                    }
                }
        )
        await interaction.response.send_message("Thanks for accepting our TOS! You are now registered!")

class blackList(discord.ui.View):
    def __init__(self, options, users):
        super().__init__(timeout=None)
        self.select_callback.options = [discord.SelectOption(label = (users[str(option)]).display_name, description = f"UID {str(option)}", value=str(option)) for option in options]
        self.select_callback.max_values = len(options)
        
    @discord.ui.select(
        placeholder = "View & Remove Users",
        min_values = 1
    )
    
    async def select_callback(self, select, interaction): 
        for i in select.values:
            db.users.update_one({"_id": interaction.user.id}, {"$pull": {"blacklist": int(i)}})
        await interaction.response.send_message(f"Removed {len(select.values)} users from your blacklist!", ephemeral=True)
        
@bot.slash_command()
async def list(ctx):
    if len((await db.users.find_one({"_id": ctx.author.id}))['blacklist']) == 0:
        return await ctx.respond("Your blacklist is empty!", ephemeral=True)
    users = {}
    for i in (await db.users.find_one({"_id": ctx.author.id}))['blacklist']:
        users[str(i)] = await bot.fetch_user(i)
    await ctx.respond("Blacklist:", view=blackList(options=(await db.users.find_one({"_id": ctx.author.id}))["blacklist"], users=users), ephemeral=True)
    
@bot.before_invoke
async def tos_check(ctx):
    if (await db.users.find_one({"_id": ctx.author.id})):
        pass
    else:
        embed=discord.Embed(
            title="Error", description="You are not registered in the database!", color=discord.Colour.red())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.add_field(name="Accept Our TOS!", value="In order to blacklist, whitelist, or use commands, you must accept our TOS.", inline=False)
        
        await ctx.respond(
            embed=embed, ephemeral=True, view=register()
        )

class Users(discord.ui.View):
    @discord.ui.user_select(min_values=1, max_values=25, placeholder="Select Users")
    async def select_callback(self, select, interaction):
        blacklist = (await db.users.find_one({"_id": interaction.user.id}))["blacklist"]
        for user in select.values:
            if user.id not in blacklist:
                db.users.update_one({"_id": interaction.user.id}, {"$push": {"blacklist": user.id}})
        await interaction.response.send_message(f"Added {', '.join([user.display_name for user in select.values if user.id not in blacklist])} to your blacklist!", ephemeral=True)

@bot.slash_command()
async def blacklist(ctx, user: discord.User = None):
    if not user: #dont be fooled, code is 100% reachable
        return await ctx.respond("Please Select Users", ephemeral=True, view=Users())
    elif user.id in (await db.users.find_one({"_id": ctx.author.id}))["blacklist"]:
        return await ctx.respond(f"{user.display_name} is already in your blacklist!", ephemeral=True)
    else:
        db.users.update_one({"_id": ctx.author.id}, {"$push": {"blacklist": user.id}})
        await ctx.respond(f"Added {user.display_name} to your blacklist!", ephemeral=True)

@bot.event
async def on_message(message):
    if message.channel.id == 1281567599272005663:
        if message.attachments:
            await message.create_thread(name=message.content or message.author.display_name)
        elif not message.attachments:
            await message.delete()

bot.run(config["TOKEN"])
import discord, motor, pymongo, asyncio, json
from motor import motor_asyncio
from discord.ext import commands
config = json.load(open("config.json"))

client = motor.motor_asyncio.AsyncIOMotorClient(f"mongodb+srv://admin:{config['DBPassword']}@cluster0.bc1nq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["affinityDB"]
class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        "self.bot.loop.create_task(self.loan_interest_loop())"

    """async def loan_interest_loop(self):
        while True:
            for user in db.users.find({}).to_list(length=None):
                if "loans" in (await db.users.find_one({"_id": user})):
                    for loan in (await db.users.find_one({"_id": user}))["loans"]:
                        if (await db.users.find_one({"_id": user}))["loans"][loan]["active"]:
                            (await db.users.find_one({"_id": user}))["loans"][loan]["owed"] += (await db.users.find_one({"_id": user}))["loans"][loan]["per"] * (await db.users.find_one({"_id": user}))["loans"][loan]["multiplier"]
                            await db.users.update_one({"_id": user}, {"$set": {(f"loans.{loan}.owed"): (await db.users.find_one({"_id": user}))["loans"][loan]["owed"]}})
            await asyncio.sleep(1)"""

    
    @commands.command(name="loan", help="Get a loan from the bank")
    async def get_loan(self, ctx, amount: int):
        if amount <= 0:
            await ctx.send("You must specify a valid amount!")
            return

        if "loans" not in (await db.users.find_one({"_id": ctx.author.id})):
            await db.users.update_one({"_id": ctx.author.id}, {"$set": {"loans": {"bank": {"active": False, "amount": 0, "interest": 0.05, "per": 500, "multiplier": 1, "owed": 0}, "school": {"active": False, "amount": 0, "interest": 0.05, "per": 1000, "multiplier": 1, "owed": 0}, "mafia": {"active": False, "amount": 0, "interest": 0.5, "per": 1800, "multiplier": 1, "owed": 0}}}})

        for loan in (await db.users.find_one({"_id": ctx.author.id}))["loans"]:
            if (await db.users.find_one({"_id": ctx.author.id}))["loans"][loan]["active"]:
                await ctx.send("You already have a loan from another source!")
                return

        if (await db.users.find_one({"_id": ctx.author.id}))["loans"]["bank"]["amount"] + amount > 50000:
            await ctx.send("You can't have more than 50000 in loans from the bank!")
            return

        (await db.users.find_one({"_id": ctx.author.id}))["loans"]["bank"]["amount"] += amount
        (await db.users.find_one({"_id": ctx.author.id}))["loans"]["bank"]["active"] = True
        await db.users.update_one({"_id": ctx.author.id}, {"$set": {"loans.bank": (await db.users.find_one({"_id": ctx.author.id}))["loans"]["bank"]}})
        await ctx.send(f"You have taken a loan of {amount} from the bank. You now owe {amount + (await db.users.find_one({'_id': ctx.author.id}))['loans']['bank']['owed']}.")

    @commands.command(name="payloan", help="Pay back your loan")
    async def pay_loan(self, ctx, amount: int):
        if amount <= 0:
            await ctx.send("You must specify a valid amount!")
            return

        if not (await db.users.find_one({"_id": ctx.author.id}))["loans"]["bank"]["active"]:
            await ctx.send("You don't have a loan from the bank!")
            return

        if amount > (await db.users.find_one({"_id": ctx.author.id}))["loans"]["bank"]["owed"]:
            await ctx.send("You don't owe that much to the bank!")
            return

        (await db.users.find_one({"_id": ctx.author.id}))["loans"]["bank"]["owed"] -= amount
        (await db.users.find_one({"_id": ctx.author.id}))["economy"]["balance"] -= amount
        await db.users.update_one({"_id": ctx.author.id}, {"$set": {"loans.bank": (await db.users.find_one({"_id": ctx.author.id}))["loans"]["bank"], "economy.balance": (await db.users.find_one({"_id": ctx.author.id}))["economy"]["balance"]}})
        await ctx.send(f"You have paid back {amount} from your loan. You now owe {(await db.users.find_one({'_id': ctx.author.id}))['loans']['bank']['owed']} to the bank.")
    
    
    @commands.command(name="balance", aliases=["bal"], help="Check your balance")
    async def check_balance(self, ctx):
        balance = (await db.users.find_one({"_id": ctx.author.id}))["economy"]["balance"]
        loans = ""
        if (await db.users.find_one({"_id": ctx.author.id}))["loans"]["bank"]["active"]:
            loans += f"Bank Loan: {(await db.users.find_one({'_id': ctx.author.id}))['loans']['bank']['owed']} coins\n"
        await ctx.send(f"Your balance is {balance} coins.\n{loans}")
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(self.loan_interest_loop())
        print(f"{self.qualified_name} cog ready!")

def setup(bot):
    bot.add_cog(Economy(bot))
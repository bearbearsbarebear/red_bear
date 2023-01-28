import discord
import asyncio
import sqlite3
from discord import app_commands

import crawler

# Change guild and channel ID
MY_GUILD = discord.Object(id=0)
MY_CHANNEL = 0

# Sqlite3 database
connect = sqlite3.connect('redbear.db')
cursor = connect.cursor()

class RedPanda(discord.Client):
	def __init__(self):
		super().__init__(intents=discord.Intents.default())

		# Bot slash commands
		self.tree = app_commands.CommandTree(self)

	async def setup_hook(self):
		self.tree.copy_global_to(guild=MY_GUILD)
		await self.tree.sync(guild=MY_GUILD)

		client.loop.create_task(client.check_novels())

	async def check_novels(self):
		await self.wait_until_ready()
		while not self.is_closed():
			updated_novels = crawler.crawl(connect, cursor)

			if updated_novels:
				for update in updated_novels:
					channel = self.get_channel(MY_CHANNEL)
					await channel.send(f"@here {update[0]} has a new chapter! Read it here: {update[1]}")

			await asyncio.sleep(20)

class Novel():
	def watch(self, interaction: discord.Interaction, link: str, name: str):
		# Check if the novel already exists in the database
		cursor.execute("SELECT * FROM watchlist WHERE Name = ? OR Link = ?", (name, link))
		result = cursor.fetchone()

		if result:
			# Novel already exists in the database
			return False
		else:
			# Novel does not exist in the database, insert it
			cursor.execute("INSERT INTO watchlist (Name, Link, Last_Chapter) VALUES (?, ?, ?)", (name, link, 1))
			connect.commit()
			return True

	def dump_db(self, interaction: discord.Interaction):
		cursor.execute("SELECT * FROM watchlist")
		watchlist_values = cursor.fetchall()

		print(watchlist_values)

	def remove(self, interaction: discord.Interaction, link: str):
		cursor.execute("SELECT * FROM watchlist WHERE Name = ?", (link,))
		novel = cursor.fetchone()

		if novel:
			cursor.execute("DELETE FROM watchlist WHERE Name = ?", (link,))
			connect.commit()
			return True
		else:
			return False

	def reduce(self, interaction: discord.Interaction):
		cursor.execute("SELECT * FROM watchlist")
		watchlist_values = cursor.fetchall()
		for row in watchlist_values:
			cursor.execute(f"UPDATE watchlist SET Last_Chapter = {row[2]-1} WHERE Name = '{row[0]}'")

		connect.commit()

client = RedPanda()
novel_functions = Novel()

@client.event
async def on_ready():
	print(f'Logged in as {client.user}:{client.user.id}')

# Sync commands from the tree
@client.tree.command()
async def sync(interaction: discord.Interaction):
	synced = await client.tree.sync()
	await interaction.response.send_message(f"Synced {len(synced)} command{'s' if len(synced) > 1 else ''} globally")

# Adds a novel in the watchlist
@client.tree.command()
@app_commands.describe(link='Link of the novel')
async def watch(interaction: discord.Interaction, link: str, name: str):
	res = novel_functions.watch(interaction, link, name)
	if res:
		await interaction.response.send_message(f"Added {name} to watchlist.")
	else:
		await interaction.response.send_message("This novel already exists in the database.")

# Dumps the whole watchlist table values
@client.tree.command()
async def dump_db(interaction: discord.Interaction):
	novel_functions.dump_db(interaction)
	await interaction.response.send_message("The database has been dumped. Check your console!")

# Remove an entry from the watchlist
@client.tree.command()
@app_commands.describe(link='Link of the novel')
async def remove(interaction: discord.Interaction, link: str):
	res = novel_functions.remove(interaction, link)
	if res:
		await interaction.response.send_message(f"Removed the entry {link} from the database.")
	else:
		await interaction.response.send_message(f"{link} not found in the database.")

# Reduce a value from every entry for debugging purposes.
# This will cause the bot to re-update every novel!
@client.tree.command()
async def reduce(interaction: discord.Interaction):
	novel_functions.reduce(interaction)
	await interaction.response.send_message("Removed one chapter from all novel entries.")

if __name__ == "__main__":
	if connect:
		client.run("BOT_TOKEN")
	else:
		print("Can't connect to the database.")
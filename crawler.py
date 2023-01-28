import sqlite3
import requests
import re
from lxml import html

def crawl(connect, cursor):
	updated_novels = []

	cursor.execute("SELECT * FROM watchlist")
	watchlist_values = cursor.fetchall()
	for row in watchlist_values:
		name = row[0]
		link = row[1]
		chapters = row[2]

		headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'}
		response = requests.get(link, headers=headers)
		tree = html.fromstring(response.content)

		value = None
		# From the xpath of the element, I do a regular expression to filter numbers and retrieve the first number
		# in the text
		if "pandanovel.org" in link:
			value = tree.xpath("/html/body/div/main/div[2]/div[1]/div/div[1]/div[3]/div[5]/ul/li[1]/a/span")
		elif "panda-novel.com" in link:
			value = tree.xpath("/html/body/div[1]/div[2]/div[1]/div/div[2]/ul/li[2]/label/strong")

		if not value:
			print(f"Couldn't find xpath of the last chapter in {link}")
			continue

		value = re.search(r'\d+', value[0].text)
		first_number = value.group()

		if int(first_number) > int(row[2]):
			cursor.execute(f"UPDATE watchlist SET Last_Chapter = {first_number} WHERE Name = '{row[0]}'")
			connect.commit()
			updated_novels.append((row[0], row[1]))

	return updated_novels
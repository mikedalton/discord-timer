# bot.py
import os, discord, sqlite3, datetime
from dateutil import parser
from dotenv import load_dotenv
from prettytable import PrettyTable

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
CHANNEL = int(os.getenv('CHANNEL'))

# Init variables
timers_db_file = "timers.db"
conn = None

# Set up timers database
if not os.path.isfile(timers_db_file):
    conn = sqlite3.connect(timers_db_file)
    conn.execute("CREATE TABLE timers (label text primary key, last_set text)")
    conn.commit()
    print("Database created")
else:
    conn = sqlite3.connect(timers_db_file)
    print("Database loaded")

def get_timers():
    timers = conn.execute("SELECT * FROM timers").fetchall()

    text_table = PrettyTable()
    
    text_table.field_names = ["Label", "Last Set"]
    text_table.align["Command"] = "l"
    text_table.align["Last Set"] = "l"

    for row in timers:
        now = datetime.datetime.utcnow()
        before = parser.parse(row[1])
        delta = now - before
        hours = divmod(delta.seconds, 3600)
        minutes = divmod(hours[1], 60)
        text_table.add_row(
            [
                row[0], '{} hours, {} minutes ago'.format(hours[0], minutes[0])
            ]
        )

    return text_table.get_string(title="Current Timers")

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.channel.id == CHANNEL:
        if message.content.startswith("!"):
            command = message.content.split(" ")
            if command[0] == "!timers":
                await message.channel.send("```" + get_timers() + "```")
            else:
                label = command[1]
                cursor = conn.cursor()
                if command[0] == "!set":
                    cursor.execute("SELECT * FROM timers WHERE label=?", [label])
                    label_row = cursor.fetchall()
                    if len(label_row) == 0:
                        conn.execute("INSERT INTO timers VALUES (?,?)", [label, datetime.datetime.utcnow()])
                        conn.commit()
                        await message.channel.send('Added `{}`'.format(label))
                    elif len(label_row) == 1:
                        conn.execute("UPDATE timers SET last_set=? WHERE label=?", [datetime.datetime.utcnow(), label])
                        conn.commit()
                        await message.channel.send('Updated `{}`'.format(label))
                    else:
                        print("Database error: too many matching rows")
                elif command[0] == "!delete":
                    cursor.execute("DELETE FROM timers WHERE label=?", [label])
                    conn.commit()
                    await message.channel.send('Deleted `{}`'.format(label))
                cursor.close()

client.run(TOKEN)
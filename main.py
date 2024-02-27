from telebot.async_telebot import AsyncTeleBot
import mysql.connector
import datetime
import asyncio
import aiofiles

# Not included the analysis algo - can't give away all the sauce for free :)
from WBAnalysisModule import ocp
from WBAnalysisModule import price
from WBAnalysisModule import get_rating
from WBAnalysisModule import pricechange

bot = AsyncTeleBot('*******')

connection = mysql.connector.connect(
    user='*******',
    password='*******',
    host='*******',
    port='25060',
    database='*******'
)
cursor = connection.cursor()


def read_tokens_from_file(filename):
    with open(filename, 'r') as file:
        tokens = [line.strip() for line in file if line.strip()]
    return tokens


def last_updated():
    query = cursor.execute(f"SELECT datetime FROM 15m WHERE `token`= 'BTC'")
    result = cursor.fetchall()
    for row in result:
        d = row[0]
    return d


def insert_into_telegram_history_table(user, input_text, output_text):
    current_datetime = datetime.datetime.now()
    sql = "INSERT INTO telegramhistory (user, input, output, datetime) VALUES (%s, %s, %s, %s)"
    values = (user, input_text, output_text, current_datetime)

    cursor.execute(sql, values)
    connection.commit()
    cursor.close()
    connection.close()


@bot.message_handler(commands=['hi', 'start', 'hello', 'begin'])
async def send_welcome(message):
    returned = f"""*Welcome to WillBear - your ultimate investment information assistant!* \n\nOur automated chatbot 
    is designed to help simplify complex financial information for users worldwide, regardless of their investment 
    experience. \n\nWith a continuous flow of expert insights and up-to-date market analysis, WillBear is your go-to 
    source for investment information and education. \n\nWhether you're a seasoned investor or just getting started, 
    our chatbot provides a wealth of information that can help guide and inform your investment decisions. \n\n_Type 
    /help to view possible commands._ """
    await bot.reply_to(message, f"""{returned}""", parse_mode="Markdown")
    insert_into_telegram_history_table(f"{message.from_user.username}", f"{message}", f"{returned}")


@bot.message_handler(commands=['ocp', 'OCP', 'o', 'O', 'Ocp'])
async def send_welcome(message):
    parts = message.text.upper().split(" ")

    if len(parts) < 3:
        returned = "Please specify both asset and interval. For example: /OCP AAPL 1d"
        await bot.reply_to(message, returned)
        insert_into_telegram_history_table(message.from_user.username, message.text, returned)
        return

    asset, interval = parts[1], parts[2]

    try:
        x = ocp(asset, interval)
        if x == "failed":
            returned = f"{asset} is not currently supported. Please try again or try /List [Sector] for some possible assets."
        else:
            returned = f"Overall Confidence Percentage for {asset} on {interval}: {x}%"


    except:
        returned = f"""The /ocp (/o) command is used to display current Overall Confidence Percentage for a certain asset.

*Command syntax:* /OCP \[Asset] \[Timeframe]

*For example:* /OCP AAPL 1d

*Output:*

_Overall Confidence Percentage for AAPL on 1d: 72.16%_

*[Asset]* - BTC, GOOG, USDGBP
*[Timeframe]* - 1m, 5m, 15m, 1h, 4h, 1d
            """
        await bot.reply_to(message, f"""{returned}""", parse_mode="Markdown")
        insert_into_telegram_history_table(f"{message.from_user.username}", f"{message}", f"{returned}")


@bot.message_handler(commands=['top', 't', 'Top', 'T', 'TOP'])
async def send_welcome(message):
    parts = message.text.split(" ")

    if len(parts) < 4:
        await bot.reply_to(message, "Usage: /Top [Number] [Market Sector] [Timeframe]")
        return

    try:
        n, sector, interval = int(parts[1]), parts[2].lower(), parts[3].lower()

        if n < 1 or n > 8:
            await bot.reply_to(message, "Please specify a number between 1 and 8.")
            return

        ocps, tokens = [], []
        for i in range(1, n + 1):
            ocp_query = f"SELECT bulltoken{i}ocp FROM tim{sector}{interval} ORDER BY id DESC LIMIT 1;"
            token_query = f"SELECT bulltoken{i} FROM tim{sector}{interval} ORDER BY id DESC LIMIT 1;"

            cursor.execute(ocp_query)
            ocps.append(cursor.fetchone()[0])

            cursor.execute(token_query)
            tokens.append(cursor.fetchone()[0])

        response_lines = [f"*Top {min(n, len(tokens))} {sector.title()} OCPs on {interval}:*"]
        response_lines += [f"{token}: {ocp}%" for token, ocp in zip(tokens, ocps)]

        response = "\n".join(response_lines)
        await bot.reply_to(message, response, parse_mode="Markdown")
        insert_into_telegram_history_table(message.from_user.username, message.text, response)

    except:
        returned = f"""The /top (/t) command is used to display the assets with the highest Overall Confidence Percentages for a certain market sector.

*Command syntax:* /Top \[Number] \[Market Sector] \[Timeframe]

*For example:* /Top 3 Forex 1h

*Output:*

_Top 3 Forex OCPs on 1h:

EURUSD: 90.19%
EURCAD: 87.56%
EURGBP: 85.23%_

*[Number]* - Assets to display (1-8)
*[Market Sector]* - Equities, Crypto, Forex
*[Timeframe]* - 15m, 1h, 4h, 1d
            """
        await bot.reply_to(message, f"""{returned}""", parse_mode="Markdown")
    insert_into_telegram_history_table(f"{message.from_user.username}", f"{message}", f"{returned}")


def execute_query(sector, interval, n, token_type):
    ocps = []
    tokens = []
    for i in range(1, n + 1):
        ocp_query = f"SELECT {token_type}token{i}ocp FROM tim{sector}{interval} ORDER BY id DESC LIMIT 1;"
        token_query = f"SELECT {token_type}token{i} FROM tim{sector}{interval} ORDER BY id DESC LIMIT 1;"

        cursor.execute(ocp_query)
        ocps.append(cursor.fetchone()[0])

        cursor.execute(token_query)
        tokens.append(cursor.fetchone()[0])

    return tokens, ocps


def format_message(tokens, ocps):
    lines = [f"{token}: {ocp}%" for token, ocp in zip(tokens, ocps)]
    return "\n".join(lines)


def bottom(interval):
    sector = "crypto"
    n = 8
    tokens, ocps = execute_query(sector, interval, n, "bear")
    return format_message(tokens, ocps)


def top(interval):
    sector = "crypto"
    n = 8
    tokens, ocps = execute_query(sector, interval, n, "bull")
    return format_message(tokens, ocps)


@bot.message_handler(commands=['Bottom', 'b', 'BOTTOM', 'B', 'bottom'])
async def send_welcome(message):
    parts = message.text.split(" ")

    if len(parts) < 4:
        await bot.reply_to(message, "Usage: /Bottom [Number] [Market Sector] [Timeframe]", parse_mode="Markdown")
        return

    try:
        num_assets = int(parts[1])
        if num_assets < 1 or num_assets > 8:
            await bot.reply_to(message, "Please specify a number of assets between 1 and 8.", parse_mode="Markdown")
            return

        sector, interval = parts[2], parts[3]
        sector_title = sector.title()
        query = f"SELECT beartoken{{}}, beartoken{{}}ocp FROM tim{sector}{interval} ORDER BY id DESC LIMIT {num_assets};"

        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            await bot.reply_to(message, "No data found. Please check your inputs and try again.", parse_mode="Markdown")
            return

        response_lines = [f"*Bottom {num_assets} {sector_title} OCPs on {interval}:*"]
        for i, (token, ocp) in enumerate(results, start=1):
            response_lines.append(f"{token}: {ocp}%")

        response_message = "\n".join(response_lines)
        await bot.reply_to(message, response_message, parse_mode="Markdown")

    except ValueError:
        await bot.reply_to(message, "Invalid number of assets. Please enter a numeric value.", parse_mode="Markdown")

    except:
        await bot.reply_to(message, f"""The /Bottom (/b) command is used to display the assets with the highest Overall Confidence Percentages for a certain market sector.

*Command syntax:* /Bottom \[Number] \[Market Sector] \[Timeframe]

*For example:* /Bottom 3 Forex 1h

*Output:*

_Bottom 3 Forex OCPs on 1h:

EURUSD: 10.19%
EURCAD: 7.56%
EURGBP: 5.23%_

*[Number]* - Assets to display (1-8)
*[Market Sector]* - Equities, Crypto, Forex
*[Timeframe]* - 15m, 1h, 4h, 1d
            """, parse_mode="Markdown")


@bot.message_handler(commands=['list', 'l', 'L', 'List', 'LIST'])
async def send_welcome(message):
    parts = message.text.split(" ")

    if len(parts) < 2:
        returned = f"""The /list (/L) command is used to display the current available assets in a certain market sector.

*Command syntax:* /List [Market Sector]

*For example:* /List Forex

*Output:*

_List of Forex Assets:

EURUSD
USDJPY
GBPUSD
AUDUSD
USDCAD
_

*[Market Sector]* - Equities, Crypto, Forex
"""
        await bot.reply_to(message, returned, parse_mode="Markdown")
        return

    sector = parts[1].lower()
    filename = f"{sector}.txt"

    try:
        if sector not in ["forex", "equities", "crypto"]:
            returned = f"""{sector.capitalize()} isn't a known market sector. 

Try Equities, Crypto, or Forex."""
            await bot.reply_to(message, returned, parse_mode="Markdown")
            return

        async with aiofiles.open(filename, mode='r') as file:
            assets = await file.read()
            returned = f"""List of Available {sector.capitalize()} Assets:

{assets}
"""
        await bot.reply_to(message, returned, parse_mode="Markdown")
        insert_into_telegram_history_table(f"{message.from_user.username}", f"{message.text}", f"{returned}")

    except FileNotFoundError:
        returned = f"""{sector.capitalize()} isn't a known market sector. 

Try Equities, Crypto, or Forex."""
        await bot.reply_to(message, returned, parse_mode="Markdown")
    except Exception as e:
        returned = f"""An unexpected error occurred while processing your request. Please try again later."""
        await bot.reply_to(message, returned, parse_mode="Markdown")

        insert_into_telegram_history_table(f"{message.from_user.username}", f"{message.text}",
                                           f"Error processing request: {str(e)}")


@bot.message_handler(commands=['majors', 'm', 'Majors', 'MAJORS', 'MAJOR', 'major', 'Major'])
async def send_welcome(message):
    try:
        parts = message.text.split(" ")
        if len(parts) < 2:
            await bot.reply_to(message, "Please specify an interval. For example: /majors 1h", parse_mode="Markdown")
            return

        interval = parts[1]
        tokens = {
            'Equities': read_tokens_from_file('equities'),
            'Crypto': read_tokens_from_file('crypto'),
            'Forex': read_tokens_from_file('forex'),
        }

        results = {}
        for category, tokens_list in tokens.items():
            results[category] = {}
            for token in tokens_list:
                try:
                    cursor.execute(f"SELECT overalloutlook FROM {interval} WHERE Token=?", (token,))
                    result = cursor.fetchone()
                    if result:
                        results[category][token] = f"{result[0]}%"
                    else:
                        results[category][token] = "Data not available"
                except Exception as e:
                    print(f"Error querying {token} in {interval}: {str(e)}")
                    results[category][token] = "Error fetching data"

        returned = f"*Top 3 Major Assets on {interval}:*\n\n"
        for category, tokens_outlook in results.items():
            returned += f"*{category}:*\n" + "\n".join(
                [f"{token} - {outlook}" for token, outlook in tokens_outlook.items()]) + "\n\n"

        await bot.reply_to(message, returned, parse_mode="Markdown")
        insert_into_telegram_history_table(f"{message.from_user.username}", message.text, returned)
    except Exception as e:
        returned = f"""The /majors (/m) command is used to display the current Overall Confidence Percentages for the largest assets in each sector.

*Command syntax:* /Majors \[Interval]

*For example:* /Majors 1h

Please ensure your command follows the correct format and try again."""
        await bot.reply_to(message, returned, parse_mode="Markdown")
        insert_into_telegram_history_table(f"{message.from_user.username}", message.text, f"Error occurred: {str(e)}")


@bot.message_handler(commands=['help', 'h', 'Help', 'HELP', 'H'])
async def send_welcome(message):
    returned = """*Welcome to the WillBear Telegram bot. *
*Here's a list of our currently available commands:*

- - - - -

*Technical Analysis Module*

_Usage: /TAM (Asset) (Interval)_

Our flagship product. Outputs a Buy/Sell signal, breaks down the confidence percentages, and gives current price data. 

E.g "_/TAM BTC 15m_" - Technical Analysis Module on Bitcoin on a 15 minute timeframe.

- - - - -

*Top Insights Module* 

_Usage: /TIM (Interval)_

Fast Data, as soon as you need it. Outputs the highest and lowest confidence assets on your specified timeframe for quick decisions. DYOR. 

E.g "_/TIM 15m_" - Top Insights Module on a 15 minute timeframe.

- - - - - 

*Ticker Oscillator Module*

_Usage: /TOM (Asset) (Interval) _

A breakdown of our algorithm. Outputs a list of different technical indicators, and their buy/sell signal. 

E.g "_/TOM BTC 15m_" - Ticker Oscillator Module on Bitcoin on a 15 minute timeframe. 

- - - - - 

*More available commands:*

_/ocp {/o}_ (Asset) (Interval)
_/top {/t}_ (Number) (Sector) (Interval)
_/bottom {/b}_ (Number) (Sector) (Interval)
_/majors {/m}_ (Intervals)
_/list {/L}_ (Sector)
_/socials {/s}_
_/help {/h}_

- - - - -

_Please click on or type in a command for additional details._ """
    await bot.reply_to(message, f"{returned}", parse_mode="Markdown")
    insert_into_telegram_history_table(f"{message.from_user.username}", f"{message}", f"{returned}")


@bot.message_handler(commands=['socials', 's', 'S', 'Socials', 'SOCIALS', 'Social', 'social', 'SOCIAL'])
async def send_welcome(message):
    returned = f"""*WillBear has an online presence all over the internet. Here are some of our platforms:* 

[WillBear.io](********)
[Twitter](https://twitter.com/********)
[Twitter (CEO)](https://twitter.com/********)
[Twitter (Bot)](https://twitter.com/********)
[Reddit](https://www.reddit.com/r/********/)
[Linkedin](https://www.linkedin.com/company/********/)
[Discord](https://discord.gg/********) 

"""
    await bot.reply_to(message, f"""{returned}""", parse_mode="Markdown")
    insert_into_telegram_history_table(f"{message.from_user.username}", f"{message}", f"{returned}")


@bot.message_handler(commands=['tam', 'TAM', 'Tam'])
async def send_welcome(message):
    parts = message.text
    part = parts.split(" ")

    try:
        asset = part[1]

        interval = "15m"
        x = ocp(asset, interval)
        if x == "failed":
            returned = f"{asset} is not currently supported. Please try again or try /List [Sector] for some possible assets. "
            await bot.reply_to(message, f"{returned}")
            insert_into_telegram_history_table(f"{message.from_user.username}", f"{message}", f"{returned}")

        else:
            m5 = ocp(asset, "5m")
            m15 = ocp(asset, "15m")
            h1 = ocp(asset, "1h")
            h4 = ocp(asset, "4h")
            d1 = ocp(asset, "1d")

            o = (m5 + m15 + h1 + h4 + d1) / 5

            f = get_rating(o)

            change = pricechange(asset, "1d")

            output = f"""
*Technical Analysis Module on {asset.upper()}:*

*Current Price:* _${format(price(asset, "1m"), ",")}_
*Price Change 1D: {change}*

*Overall Confidence Percentages: *
5m: _{m5}%_
15m: _{m15}%_
1h: _{h1}%_
4h: _{h4}%_
1d: _{d1}%_

{asset.upper()} Outlook: {round(o, 2)}% - *{f}*
"""

            await bot.reply_to(message, f"{output}", parse_mode="Markdown")
            insert_into_telegram_history_table(f"{message.from_user.username}", f"{message}", f"{output}")

    except:
        returned = f""""""
        await bot.reply_to(message, f"""{returned}""", parse_mode="Markdown")
        insert_into_telegram_history_table(f"{message.from_user.username}", f"{message}", f"{returned}")


@bot.message_handler(commands=['tim', 'TIM', 'Tim'])
async def send_welcome(message):
    parts = message.text
    part = parts.split(" ")

    try:
        interval = part[1]

        if interval.lower() not in ["1m", "5m", "15m", "1h", "4h", "1d"]:
            returned = f"{interval} is not currently supported. Please try again. "
            await bot.reply_to(message, f"{returned}")
            insert_into_telegram_history_table(f"{message.from_user.username}", f"{message}", f"{returned}")

        else:
            topmes = top(interval)
            bottommes = bottom(interval)
            last = last_updated()
            output = f"""
*Top Insights Module for Crypto on {interval}:*

*Highest Confidence Assets*
{topmes}

*Lowest Confidence Assets*
{bottommes}

_Last Updated: {last}_
"""

            await bot.reply_to(message, f"{output}", parse_mode="Markdown")
            insert_into_telegram_history_table(f"{message.from_user.username}", f"{message}", f"{output}")

    except:
        interval = "1d"
        topmes = top(interval)
        bottommes = bottom(interval)
        last = last_updated()
        returned = f"""        
*Top Insights Module for Crypto on {interval}:*

*Highest Confidence Assets*
{topmes}

*Lowest Confidence Assets*
{bottommes}

_Last Updated: {last}_
_No interval specified, defaulting to 1 day._        
"""
        await bot.reply_to(message, f"""{returned}""", parse_mode="Markdown")
        insert_into_telegram_history_table(f"{message.from_user.username}", f"{message}", f"{returned}")


@bot.message_handler(func=lambda message: True)
async def echo_message(message):
    returned = f""""{message.text}" is not an available command. 

Try again or type /help for a list of possible commands. """
    await bot.reply_to(message, f'{returned}')
    insert_into_telegram_history_table(f"{message.from_user.username}", f"{message}", f"{returned}")


asyncio.run(bot.polling())
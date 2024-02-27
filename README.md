# WillBear Telegram Bot

## Overview
The WillBear Telegram Bot was an early version of the user platform based on the WillBear algorithms. This bot is designed to provide users with financial data analysis straight to their phone. It offers a range of commands allowing users to query financial data, including price movements, confidence percentages, and asset listings.

![Screenshot](https://i.imgur.com/S0SDWo8.png)

Above is a screenshot from a later version of the WillBear platform. Built using HTML, CSS, JS, PHP, MySQL

## Features
- **Financial Data Analysis**: Retrieve and analyse financial data using custom algorithms (note: algorithms are proprietary and not included in this code).
- **Data Retrieval**: Fetch the latest forex, equities, or cryptocurrency data and financial metrics from a MySQL database.
- **User Interaction Logging**: Log each interaction to a database for audit and improvement purposes.
- **Command Handling**: Process various commands like `/start`, `/ocp`, `/top`, `/bottom`, and `/list` to provide financial insights.

## Prerequisites
- Python 3.8 or newer
- `aiogram` library for asynchronous bot operation
- `mysql.connector` for database interactions
- `aiofiles` for asynchronous file operations
- Access to a MySQL database with the required schema
- A Telegram bot token (obtainable from BotFather on Telegram)


## Setup
1. Ensure Python 3 is installed on your system.
2. Install the needed packages using pip:
   ```bash
   pip install aiogram mysql-connector aiofiles
   ```
3. Insert your Telegram API key in the script.

## Usage
After starting the bot, users can interact with it by sending commands through a Telegram chat interface. Below are some of the supported commands:

- `/start`, `/hi`, `/hello`, `/begin` - Welcome message and basic instructions.
- `/ocp [ASSET] [INTERVAL]` - Fetches the Overall Confidence Percentage for a specified asset over a given interval.
- `/top [NUMBER] [MARKET SECTOR] [TIMEFRAME]` - Retrieves the top N assets based on their OCP in a specified market sector and timeframe.
- `/bottom [NUMBER] [MARKET SECTOR] [TIMEFRAME]` - Similar to `/top`, but fetches the bottom N assets.
- `/list [MARKET SECTOR]` - Lists available assets in a given market sector.

import aiohttp
import asyncio
import datetime
import json
import sys
from rich.console import Console
from rich.table import Table
from rich import box


async def fetch_exchange_rate(session, date):
    url = f'https://api.privatbank.ua/p24api/exchange_rates?json&date={date}'
    async with session.get(url) as response:
        data = await response.text()
        return json.loads(data)


async def get_exchange_rates(dates):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_exchange_rate(session, date) for date in dates]
        return await asyncio.gather(*tasks)


def format_result(data, currencies):
    formatted_result = []

    for entry in data:
        result_entry = {entry['date']: {}}

        for currency in currencies:
            rates = entry['exchangeRate']
            currency_rates = {
                'sale': next((rate['saleRate'] for rate in rates if rate['currency'] == currency), 'N/A'),
                'purchase': next((rate['purchaseRate'] for rate in rates if rate['currency'] == currency), 'N/A')
            }
            result_entry[entry['date']][currency] = currency_rates

        formatted_result.append(result_entry)

    return formatted_result


def create_table(data):
    table = Table(box=box.SIMPLE)
    table.add_column("Date", style="cyan", no_wrap=True, width=15)
    table.add_column("Currency", style="cyan", no_wrap=True, width=10)
    table.add_column("Sale Rate", style="magenta", width=15)
    table.add_column("Purchase Rate", style="magenta", width=15)

    for entry in data:
        for date, rates in entry.items():
            for currency, values in rates.items():
                table.add_row(
                    f"{date}",
                    f"{currency}",
                    f"{values['sale']:.4f}",
                    f"{values['purchase']:.4f}"
                )

    table.row_styles = ["", "dim"]
    return table


def main():
    num_days = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    num_days = min(num_days, 10)

    today = datetime.date.today()
    date_range = [today - datetime.timedelta(days=i) for i in range(num_days)]

    loop = asyncio.get_event_loop()
    exchange_rates = loop.run_until_complete(get_exchange_rates(
        [date.strftime("%d.%m.%Y") for date in date_range]))

    currencies_to_fetch = ['EUR', 'USD']
    result = format_result(exchange_rates, currencies_to_fetch)

    console = Console()
    table = create_table(result)
    console.print(table)


if __name__ == "__main__":
    main()

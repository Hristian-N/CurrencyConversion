import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation
import requests
import json

def load_api_key(config_file='config.json'):
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config['API_KEY']

API_KEY = load_api_key()
BASE_URL = 'https://api.fastforex.io'

def validate_date(date_str):
    try:
        # Attempt to parse the date string into a datetime object
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        # Raise an error if the date format is incorrect
        raise argparse.ArgumentTypeError(f"Invalid date format: '{date_str}'. Use YYYY-MM-DD format.")

def is_valid_amount(number):
    try:
        decimal_number = Decimal(str(number))
        return abs(decimal_number.as_tuple().exponent) == 2
    except (ValueError, InvalidOperation):
        return False

def get_currencies(currency_code):
    endpoint = f'{BASE_URL}/currencies'
    params = {
        'api_key': API_KEY
    }

    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return response.text

def is_currency_present():
    while True:
        currency_code = input("Enter currency code: ").upper()

        if currency_code == "END":
            exit()

        currencies = get_currencies(currency_code)
        if currencies and 'currencies' in currencies and currency_code in currencies['currencies']:
            return currency_code
        else:
            print("Please enter a valid currency code")

def convert(base_currency, target_currencies):

    endpoint = f'{BASE_URL}/time-series'

    params = {
        'from': base_currency,
        'to': target_currencies,
        'interval': 'P1D',
        'api_key': API_KEY
    }

    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return response.text


def find_value_on_date(date, target_currency_code, data):
    results = data['results']
    dates = results[target_currency_code.upper()]

    if date in dates:
        print(dates[date])
        return dates[date]

    for key, value in dates.items():
        if key == date.strftime('%Y-%m-%d'):
            return value

    print("Date not found in the data.")
    return None


def main(args):

    while True:

        # Amount
        while True:
            amount = input("Amount: ")

            if amount.upper() == "END":
                exit()
            elif is_valid_amount(amount):
                break
            else:
                print("Please enter a valid amount")

        # Base Currency
        base_currency_code = is_currency_present()

        # Target Currency
        target_currency_code = is_currency_present()

        # Find value for the chosen date
        value = find_value_on_date(args.date, target_currency_code, convert(base_currency_code, target_currency_code))
        # calculate
        print(round(float(amount) * value, 2))
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a date argument.")
    parser.add_argument('date', type=validate_date, help="Date in YYYY-MM-DD format")

    args = parser.parse_args()

    main(args)

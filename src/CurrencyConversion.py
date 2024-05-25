import argparse
import os
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
cache = {}
json_filename = 'results.json'

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

def get_currencies():
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
        currency_code = input("").upper()

        if currency_code == "END":
            exit()

        currencies = get_currencies(currency_code)
        if currencies and 'currencies' in currencies and currency_code in currencies['currencies']:
            return currency_code
        else:
            print("Please enter a valid currency code")

def convert(base_currency_code, target_currency_code):
    if base_currency_code in cache and target_currency_code in cache[base_currency_code]['results']:
        return cache[base_currency_code]

    endpoint = f'{BASE_URL}/time-series'

    params = {
        'from': base_currency_code,
        'to': target_currency_code,
        'interval': 'P1D',
        'api_key': API_KEY
    }

    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        data = response.json()
        # Merge with existing data if base currency is already in cache
        if base_currency_code in cache:
            existing_data = cache[base_currency_code]
            for key, value in data['results'].items():
                if key in existing_data['results']:
                    existing_data['results'][key].update(value)
                else:
                    existing_data['results'][key] = value
        else:
            cache[base_currency_code] = data
        return data
    else:
        return response.text


def find_value_on_date(date, target_currency_code, data):

    results = data['results']
    dates = results[target_currency_code.upper()]

    if date in dates:
        return dates[date]

    for key, value in dates.items():
        if key == date.strftime('%Y-%m-%d'):
            return value

    print("Date not found in the data.")
    return None


def save_to_json(base_currency, target_currency, amount, converted_amount, date):
    log = {
        "base_currency": base_currency,
        "target_currency": target_currency,
        "amount": amount,
        "converted_amount": converted_amount,
        "date": date.strftime('%Y-%m-%d')
    }

    if os.path.exists(json_filename):
        with open(json_filename, 'r') as file:
            data = json.load(file)
    else:
        data = []

    data.append(log)

    with open(json_filename, 'w') as file:
        json.dump(data, file, indent=4)


def main(args):

    while True:

        # Amount
        while True:
            amount = input("")

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

        json_data = convert(base_currency_code, target_currency_code)

        value = find_value_on_date(args.date, target_currency_code, json_data)

        # calculate
        result = str(amount) + " " + base_currency_code.upper() + " is " + str(
            round(float(amount) * value, 2)) + " " + target_currency_code.upper()
        print(result)
        print()
        save_to_json(base_currency_code, target_currency_code, amount, result, args.date)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a date argument.")
    parser.add_argument('date', type=validate_date, help="Date in YYYY-MM-DD format")

    args = parser.parse_args()

    main(args)

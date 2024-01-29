from datetime import datetime

import numpy as np
import pandas as pd
import scipy
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

urls = {
    "shortterm": "https://markets.businessinsider.com/bonds/finder?{}borrower=71&maturity=shortterm&yield=&bondtype=2"
                 "%2c3%2c4%2c16&coupon=&currency=184&rating=&country=19",
    "midterm": "https://markets.businessinsider.com/bonds/finder?{}borrower=71&maturity=midterm&yield=&bondtype=2"
               "%2c3%2c4%2c16&coupon=&currency=184&rating=&country=19"
}

base_url = "https://markets.businessinsider.com"


def plot_coupon_issue(df):
    fig, ax = plt.subplots(figsize=(10, 6))

    # Colormap normalization
    norm = Normalize(vmin=df['Maturity Year'].min(), vmax=df['Maturity Year'].max())
    sm = ScalarMappable(cmap='viridis', norm=norm)
    sm.set_array([])

    scatter = ax.scatter(df['Issue Year'], df['Coupon'], marker='o',
                         label='Coupon Percent (Issue)', c=df['Maturity Year'], cmap='viridis')

    cbar = plt.colorbar(sm, ax=ax, label='Maturity Year')
    ax.set_xlabel('Issue Date')
    ax.set_ylabel('Coupon %')
    ax.set_title('Coupon % vs. Issue Year (Colored by Maturity Year)')
    ax.grid(True)
    plt.show()


def get_ytm(df):
    _sum = (df["Par Value"] + df["Bond Price"]) / pd.to_numeric(df["Compounding Periods"])
    _diff = (df["Par Value"] - df["Bond Price"]) / 2
    _coupon = df["Coupon Payment"] * 2
    return (_coupon + _sum) / _diff


def interpolation(x1, x2, y1, y2, x):
    return y1 + (x - x1) * ((y2 - y1) / (x2 - x1))


def get_payments(year):
    year = round(year, 2)
    payments = {year}
    while year > 0.5:
        year -= 0.5
        payments.add(round(year, 2))
    return payments


def get_bonds(data):
    data["Maturity Date"] = pd.to_datetime(data["Maturity Date"], format="mixed").dt.strftime('%Y-%m-%d')
    data["Issue Date"] = pd.to_datetime(data["Issue Date"], format="mixed").dt.strftime('%Y-%m-%d')

    data1 = data[pd.to_datetime(data["Maturity Date"], format="mixed").dt.month == 3]
    data2 = data[pd.to_datetime(data["Maturity Date"], format="mixed").dt.month == 9]

    data = pd.concat([data1, data2], axis=0, ignore_index=True)

    return data


def binary_search(lst, target):
    left, right = 0, len(lst) - 1
    while left <= right:
        mid = left + (right - left) // 2
        if lst[mid] == target:
            return mid
        elif lst[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return left - 1


def get_interpolation(rates, time):
    x = list(rates.keys())
    idx = binary_search(sorted(x), time)
    x1 = x[idx]
    x2 = x[idx + 1 if idx < len(x) - 1 else idx - 1]
    y1, y2 = rates[x1], rates[x2]
    return interpolation(x1, x2, y1, y2, time)


def zero_coupon_bonds(df):
    zero_df = df[df["Months to Maturity"] < 6.0]
    non_zero_df = df[df["Months to Maturity"] >= 6.0]
    zero_df["Zero_Yield"] = np.log((zero_df["Par Value"] + zero_df["Coupon Payment"]) / zero_df["Dirty Price"]) / \
                            zero_df["Months to Maturity"]

    df = pd.concat([non_zero_df, zero_df], ignore_index=True, axis=0)
    return df


def generate_range():
    start_date = pd.to_datetime('2024-02-05', format="%Y-%m-%d")
    end_date = start_date + pd.DateOffset(years=5)

    date_ranges = pd.date_range(start=start_date, end=end_date, periods=10)

    return date_ranges.tolist()


def plot_bonds_price(df):
    plt.figure(figsize=(30, 10))
    sns.scatterplot(x='Maturity Date', y='Bond Price', data=df)

    for i, row in df.iterrows():
        plt.text(row['Maturity Date'], row['Bond Price'], f'{row["ISIN"]}', fontsize=8, ha='right', va='bottom')

    plt.title('Bond Price vs. Maturity Date')
    plt.xlabel('Maturity Date')
    plt.ylabel('Price')
    plt.xticks(rotation=45)

    for target_date in generate_range():
        plt.axvline(x=target_date, color='red', linestyle='--', label=f'{target_date}')

    plt.legend()

    plt.grid(True)
    plt.show()


def years_to_maturity(issue_date, maturity_date):
    issue_date = datetime.strptime(issue_date, '%m/%d/%Y')
    maturity_date = datetime.strptime(maturity_date, '%m/%d/%Y')

    time_to_maturity = int((maturity_date - issue_date).days / 365.2425)
    return time_to_maturity


def calculate_num_compounding_periods(coupon_rate, num_years):
    return num_years * coupon_rate


def calculate_semi_annual_coupon_rate(coupon_rate):
    return coupon_rate / 2


def calculate_semi_annual_coupon(coupon_rate, face_value):
    return coupon_rate * face_value


def closest_values(target, lst):
    sorted_list = sorted(lst, key=lambda x: abs(x - target))

    closest_greater = sorted_list[len(lst) - 1]
    closest_smaller = 0

    for value in sorted_list:
        if value > target:
            closest_greater = min(value, closest_greater)

    for value in reversed(sorted_list):
        if value < target:
            closest_smaller = max(value, closest_smaller)

    return closest_smaller, closest_greater

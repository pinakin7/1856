import math
import random
from typing import Set, Any
from utils import closest_values
import numpy as np
import pandas as pd
from scipy.optimize import brentq

def linear_interpolation(time_1, yield_1, time_2, yield_2, time):
    return yield_1 + (time - time_1) * ((yield_2 - yield_1) / (time_2 - time_1))


class Bond:

    def __init__(self, data, date):
        self.start_date = pd.to_datetime(date, format='mixed')
        self.isin = data["ISIN"]
        self.coupon = data["Coupon"]
        self.price = data["Ask"]
        self.par = 100 + (self.coupon / 2)
        self.issue = pd.to_datetime(data["Issue Date"], format="mixed")
        self.maturity = pd.to_datetime(data["Maturity Date"], format="mixed")
        self.number_days_last_payment = (self.start_date - pd.to_datetime("09/01/2023", format="%m/%d/%Y")).days
        self.coupon_payment = self.coupon * self.par / 200
        self.maturity_months = int((self.maturity - self.start_date).days / 30)
        self.dirty_price = self.get_dirty_price()
        self.payments = sorted(self.get_payments())
        self.is_zero_coupon = self.maturity_months <= 6
        self.frequency = 2
        self.ytm = None
        self.coupon_terms = (self.maturity - self.issue).days // 360

    def get_dirty_price(self) -> float:
        return (self.number_days_last_payment / 360) * self.coupon + self.price

    def get_payments(self) -> set[Any]:
        payments = {self.maturity_months}
        months = self.maturity_months
        while months > 6:
            months -= 6
            payments.add(months)
        return payments

    def bond_price(self, ytm):
        price = 0
        price = sum([self.coupon / (1 + ytm / self.frequency) ** (self.frequency * t) for t in
                     range(1, self.coupon_terms * self.frequency + 1)])
        price += self.par / (1 + ytm / self.frequency) ** (ytm * self.frequency)
        return price

    def calculate_ytm(self):
        def price_diff(ytm):
            return self.bond_price(ytm) - (self.coupon*(self.coupon_terms-1) + self.par)

        ytm_guess = self.coupon / self.price  # Initial guess for YTM based on current price and coupon rate
        self.ytm = brentq(price_diff, a=0, b=1, xtol=1e-5)  # Use Brent's method to find the root

    def get_bond_dict(self):
        return {
        "ISIN": self.isin,
        "Coupon": self.coupon,
        "Price": self.price,
        "Par": self.par,
        "Issue Date": self.issue,
        "Maturity Date": self.maturity,
        "Coupon Payment": self.coupon_payment,
        "Days Since Last Payment": self.number_days_last_payment,
        "Maturity Month": self.maturity_months,
        "Dirty Price": self.dirty_price,
        "Payments": self.payments,
        "Yield to Maturity": getattr(self, 'ytm', None)  # Use getattr to handle missing 'ytm' attribute gracefully
    }

    def __repr__(self):
        return f"{self.__class__.__name__}(" \
               f"isin={self.isin!r}, " \
               f"coupon={self.coupon!r}, " \
               f"price={self.price!r}, " \
               f"par={self.par!r}, " \
               f"issue={self.issue!r}, " \
               f"maturity={self.maturity!r}, " \
               f"coupon_payment={self.coupon_payment!r}, " \
               f"number_days_last_payment={self.number_days_last_payment!r}, " \
               f"maturity_month={self.maturity_months!r}, " \
               f"dirty_price={self.dirty_price!r}, " \
               f"payments={self.payments!r}),"\
                f"Yield to Maturity={self.ytm!r}"


class Bonds:
    def __init__(self, df, date):
        self._bonds = list()
        self.zero_coupon = None
        self._yield = {0: 0}
        self.forward_rates = {}
        self.get_bonds(df, date)
        self._bonds = sorted(self._bonds, key=lambda bond: bond.maturity_months)
        self.get_zero_coupon_yield()
        self.bootstrap_yield_curve()
        self.interpolate_years()
        self.get_forward_rate(initial_period=12, periods=[24, 36, 48, 60])

    def get_zero_coupon_yield(self):
        self._yield[self.zero_coupon.maturity_months] = 12 * np.log(
            self.zero_coupon.par / self.zero_coupon.dirty_price) / self.zero_coupon.maturity_months

    def bootstrap_yield_curve(self):
        for bond in self._bonds:
            discounted_cash_flow = bond.dirty_price
            for month in bond.payments[:-1]:
                if not month in self._yield:
                    m1, m2 = closest_values(month, self._yield.keys())
                    self._yield[month] = linear_interpolation(m1, self._yield[m1], m2, self._yield[m2], month)

                discounted_cash_flow -= bond.coupon_payment * np.exp(-self._yield[month] * month / 12)
            self._yield[bond.maturity_months] = 12 * np.log(bond.par / discounted_cash_flow) / bond.maturity_months

    def get_bonds(self, df, date) -> None:
        for idx in df.index:
            bond = Bond(df.iloc[idx], date)
            if not bond.is_zero_coupon:
                self._bonds.append(bond)
            else:
                self.zero_coupon = bond

    def get_forward_rate(self, initial_period, periods):
        for period in periods:
            rate = 12 * (self._yield[period] * (period / 12) - self._yield[initial_period] * (initial_period / 12)) / (
                    period - initial_period)
            self.forward_rates[(initial_period, period)] = rate

    def interpolate_years(self):
        for year in [12, 24, 36, 48, 60]:
            if year not in self._yield:
                y1, y2 = closest_values(year, self._yield.keys())
                self._yield[year] = linear_interpolation(y1, self._yield[y1], y2, self._yield[y2], year)


    def get_bond_ytm(self):
        for bond in self._bonds:
            bond.calculate_ytm()
            print(f"Bond:{bond.isin}, YTM:{bond.ytm}")


    def get_bonds_dataframe(self):
        df = []
        for bond in self._bonds:
            df.append(bond.get_bond_dict())
        df = pd.DataFrame(df)
        df.sort_values(by='Maturity Date', inplace=True)

        df.reset_index(drop=True, inplace=True)
        return df


def get_log_yield(data):
    log_yield = np.zeros((6,10))
    keys = list(data.keys())
    for j in range(9):
        bonds = data[keys[j]]
        for i in range(1,5):
            log_yield[i][j] = np.log(data[keys[j+1]]._yield[i*12]/bonds._yield[i*12])
    return np.cov(log_yield, rowvar=True)


def get_log_forward(data):
    log_yield = np.zeros((6, 10))
    keys = list(data.keys())
    initial_period = 12
    for j in range(9):
        bonds = data[keys[j]]
        for i in range(1, 5):
            log_yield[i][j] = np.log(data[keys[j + 1]].forward_rates[(12, (i+1) * 12)] / bonds.forward_rates[(initial_period, (i+1) * 12)])
    return np.cov(log_yield, rowvar=True)


def eigen_decomposition(cov_matrix):
    eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
    return eigenvalues, eigenvectors
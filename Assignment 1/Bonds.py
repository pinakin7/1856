import math
from typing import Set, Any
from utils import closest_values
import numpy as np
import pandas as pd


def linear_interpolation(time_1, yield_1, time_2, yield_2, time):
    return yield_1 + (time - time_1) * ((yield_2 - yield_1) / (time_2 - time_1))


class Bond:
    start_date = pd.to_datetime('2023-10-01', format='%Y-%m-%d')

    def __init__(self, data):
        self.isin = data["ISIN"]
        self.coupon = data["Coupon"]
        self.price = data["Bond Price"]
        self.par = 100 + self.coupon / 2
        self.issue = data["Issue Date"]
        self.maturity = data["Maturity Date"]
        self.coupon_payment = self.coupon * self.par / 200
        self.number_days_last_payment = 1
        self.maturity_months = math.floor((self.maturity - self.start_date).days / 30)
        self.dirty_price = self.get_dirty_price()
        self.payments = sorted(self.get_payments())

    def get_dirty_price(self) -> float:
        return (self.number_days_last_payment / 360) * self.coupon + self.price

    def get_payments(self) -> set[Any]:
        payments = {self.maturity_months}
        m = self.maturity_months
        while m > 6:
            m -= 6
            payments.add(m)
        return payments

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
               f"maturity_months={self.maturity_months!r}, " \
               f"dirty_price={self.dirty_price!r}, " \
               f"payments={self.payments!r})"


class Bonds:
    def __init__(self, df):
        self._bonds = list()
        self._yield = {0: 0}
        self.forward_rates = [[0]*12*5]*5
        self.get_bonds(df)
        self.bootstrap_yield_curve()
        self.interpolate_years()
        self.get_forward_rate()

    def bootstrap_yield_curve(self):
        # calculate the yield curve via bootstrapping and linear interpolation whenever required
        for bond in self._bonds:
            # checking for the zero coupon bond
            if len(bond.payments) == 1:
                self._yield[bond.payments[0]] = (bond.payments[0] / 12) * np.log(bond.par / bond.dirty_price)
            else:
                _price = bond.dirty_price
                for year in bond.payments:
                    if year != bond.payments[-1]:
                        if year not in self._yield.keys():
                            y1, y2 = closest_values(year, self._yield.keys())
                            self._yield[year] = linear_interpolation(y1, self._yield[y1], y2, self._yield[y2], year)
                        _price -= bond.coupon_payment * np.exp(-self._yield[year] * (year / 12))
                    else:
                        self._yield[year] = (year / 12) * np.log(bond.par / bond.dirty_price)

    def get_bonds(self, df) -> None:
        for idx in df.index:
            self._bonds.append(Bond(df.iloc[idx]))

    def get_forward_rate(self):
        year_1 = self._yield[12]
        for day in range(12*4):
            self.forward_rates[1][day] = (self._yield[12+day]*(12+day) - year_1*12)/day


    def interpolate_years(self):
        for year in range(1,59):
            y1, y2 = closest_values(year, self._yield.keys())
            self._yield[year] = linear_interpolation(y1, self._yield[y1], y2, self._yield[y2], year)




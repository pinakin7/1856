import logging
import os

import numpy as np
import pandas as pd
import glob
from utils import get_bonds

def process_csv_files(base_dir, save_dir):
    midterm_files_pattern = f'{base_dir}/midterm/*.csv'
    shortterm_files_pattern = f'{base_dir}/shortterm/*.csv'

    midterm_files = glob.glob(midterm_files_pattern)
    shortterm_files = glob.glob(shortterm_files_pattern)

    for file in shortterm_files:
        file_name = file.split("\\")[-1]
        data = pd.read_csv(file)
        data['Coupon'] = data['Coupon'].str.rstrip('%').astype('float')
        data["Maturity Date"] = pd.to_datetime(data["Maturity Date"], format="%m/%d/%Y")
        data["Issue Date"] = pd.to_datetime(data["Issue Date"], format="%m/%d/%Y")
        data.to_csv(os.path.join(base_dir, f"{save_dir}/{file_name}"), index=False)

    for file in midterm_files:
        file_name = file.split("\\")[-1]
        prev_data = pd.read_csv(os.path.join(base_dir, f"{save_dir}/{file_name}"))
        data = pd.read_csv(file)
        data['Coupon'] = data['Coupon'].str.rstrip('%').astype('float')
        data["Maturity Date"] = pd.to_datetime(data["Maturity Date"], format="%m/%d/%Y")
        data["Issue Date"] = pd.to_datetime(data["Issue Date"], format="%m/%d/%Y")

        df = pd.concat([prev_data, data], ignore_index=True, axis=0)
        df = df.drop(columns=["Moody's Rating", "Bid", "Yield"], axis=1)

        df = get_bonds(df)

        df.to_csv(os.path.join(base_dir, f"{save_dir}\\{file_name}"), index=False)

if __name__ == "__main__":
    process_csv_files(base_dir="data", save_dir="final")

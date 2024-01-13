import logging
import os

import pandas as pd


def generate_final_data(data_dir="data", save_dir="data.csv"):
    data = None
    for root, dirs, files in os.walk(data_dir):
        if files:
            for file in files:
                logging.log(60, "Processing file: {}".format(file))
                if file.endswith(".csv") and file != "data.csv":
                    df = pd.read_csv(os.path.join(root, file), index_col='ISIN')
                    data = df if data is None else pd.concat([data, df], ignore_index=False, axis=0)
    logging.log(60, "Finished processing")
    data['Coupon'] = data['Coupon'].str.rstrip('%').astype('float')
    data['Maturity Date'] = pd.to_datetime(data['Maturity Date'], format='mixed')
    data['Issue Date'] = pd.to_datetime(data['Issue Date'], format='mixed')
    data['Bond Days'] = (data['Maturity Date'] - data['Issue Date']).dt.days
    data['Bond Months'] = data['Bond Days']/30
    data['Bond Years'] = data['Bond Months']/12
    data.to_csv(os.path.join(data_dir, save_dir))


if __name__ == "__main__":
    generate_final_data()

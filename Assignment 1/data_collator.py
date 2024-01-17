import logging
import os

import pandas as pd


def generate_final_data(data_dir="data", save_dir="data.csv"):
    data = None
    for root, dirs, files in os.walk(data_dir):
        if files:
            for file in files:
                logging.log(60, "Processing file: {}".format(file))
                if file.endswith(".csv") and file not in {'data.csv', 'cleaned_data.csv', 'final_data.csv'}:
                    df = pd.read_csv(os.path.join(root, file))
                    data = df if data is None else pd.concat([data, df], ignore_index=True, axis=0)
    logging.log(60, "Finished processing")
    data['Coupon'] = data['Coupon'].str.rstrip('%').astype('float')
    data['Bond Price'] = data['Bid']
    data.to_csv(os.path.join(data_dir, save_dir), index=False)


if __name__ == "__main__":
    generate_final_data()

from datetime import date
import logging
import pandas as pd
import requests
from bs4 import BeautifulSoup
from utils import urls, base_url


def extract_table(url):
    response = requests.get(url)
    if response.status_code == 200:
        logging.log(60, f'Crawling into the bond data')
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        isin, issue_date = "", ""
        if table:
            # Assuming the structure is simple, iterate through table rows
            for row in table.find_all('tr'):
                columns = row.find_all('td')
                if len(columns) == 2:
                    label = columns[0].text.strip()
                    value = columns[1].text.strip()

                    if label == 'ISIN':
                        isin = value
                    elif label == 'Issue Date':
                        issue_date = value

            # Print or use the extracted data
            return isin, issue_date
        else:
            print("No table found on the linked page.")
    else:
        raise ValueError("No page found")


def extract_isin(str):
    return str.split("-")[-1].split("?")[0]


def scrape_data(soup):
    table = soup.find('table')
    if table:
        logging.log(60, f'Found Table Data')
        data = []
        rows = table.find_all('tr')
        if rows:
            for row in rows:
                columns = row.find_all(['td', 'th'])
                if columns:
                    logging.log(60, f'Found row with data')
                    row_data = [column.text.strip() for column in columns]
                    link = columns[0].find('a')
                    if link:
                        isin, issue_date = extract_table(f"{base_url}/{link['href']}")
                        row_data[0] = isin
                        row_data.append(issue_date)
                    else:
                        row_data[0] = "ISIN"
                        row_data.append("Issue Date")
                    data.append(row_data)
                else:
                    return None
            return data
        else:
            raise Exception('No row found')
    else:
        raise ValueError("No data found")


def crawler(url):
    response = requests.get(url)
    if response.status_code == 200:
        logging.log(60, f'Crawling')
        soup = BeautifulSoup(response.text, 'html.parser')
        return scrape_data(soup)
    else:
        return None


def scrape_market_insider(save_path="data"):
    for url in urls:
        logging.log(60, f"Scraping {url}")
        i = 1
        data = None
        while True:
            logging.log(60, f"Into page {i}")
            page = f"p={i}&" if i > 1 else ""
            curr_data = crawler(urls[url].format(page))
            if curr_data:
                i += 1
                logging.log(60, f"Creating dataframe for page {i}")
                curr_data = pd.DataFrame(curr_data[1:], columns=curr_data[0])
                data = curr_data if data is None else pd.concat([data, curr_data], ignore_index=True, axis=0)
            else:
                break
        logging.log(60, f"Scraping complete for {url} {date.today().strftime('%B %d %Y')} saving into csv file.")
        data.to_csv(f"{save_path}/{url}/{date.today().strftime('%B %d %Y')}.csv", index=False)


if __name__ == "__main__":
    scrape_market_insider("data")

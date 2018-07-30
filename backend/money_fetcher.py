import pandas as pd
import datetime
import time
import os
import shutil

from bson import ObjectId
from scrapy import Selector

import pymongo
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options


def create_default_client(username="etl_user", password="etl360"):
    uri = "mongodb://%s:%s@%s" % (
        quote_plus(username), quote_plus(password), "192.168.44.101:27100")
    return pymongo.MongoClient(uri)

def str_to_date(s):
    return datetime.datetime.strptime(s, '%d-%b-%Y')


def parse_imf_xml(xml_file):
    rows = []
    f = open(xml_file)
    selector = Selector(text=f.read(), type='xml')
    root = selector.xpath("//EFFECTIVE_DATE")
    for element in root:
        date = element.xpath("./@VALUE").extract_first()
        date = str_to_date(date).strftime("%Y%m%d")
        for rate in element.xpath(".//RATE_VALUE"):
            iso_code = rate.xpath("./@ISO_CHAR_CODE").extract_first()
            value = rate.xpath("./text()").extract_first()
            if value == "Blank":
                value = None
            rows.append([date, iso_code, value])
    origin_df = pd.DataFrame(rows, columns=["date", "currency_code", "rate"])
    max_date = origin_df['date'].max()
    min_date = origin_df['date'].min()
    currency_codes = origin_df["currency_code"].unique()
    new_rows = []
    for year in range(int(min_date[:4]), int(max_date[:4]) + 1):
        for month in range(int(min_date[4:6]), int(max_date[4:6]) + 1):
            for day in range(int(min_date[6:8]), int(max_date[6:8]) + 1):
                date = str(year) + str(month).rjust(2, '0') + str(day).rjust(2, '0')
                if not origin_df[origin_df['date'] == date].empty:
                    continue
                for code in currency_codes:
                    new_rows.append(pd.Series({"date": date, "currency_code": code}, index=list(origin_df.columns)))
    new_df = pd.DataFrame(new_rows)
    full_df = pd.concat([origin_df, new_df]).sort_values("date")
    df_groups = []
    for index, group_df in full_df.groupby("currency_code"):
        df_groups.append(group_df.fillna(method='pad').fillna(method='bfill'))
    finally_df = pd.concat(df_groups)
    return finally_df


def insert_new_rate_to_mongo(collection, finally_df):
    for index, row in finally_df.iterrows():
        date, currency_code, rate = str(row["date"]), row["currency_code"], round(float(row["rate"]), 4)
        obj_id = ObjectId(bytes("-".join([date, currency_code]).encode()))
        collection.update({"_id": obj_id}, {"$set": {
            "currency_code": currency_code,
            "date": date,
            "rate": rate}}, upsert=True)


def run():
    fpath = r"D:\\imf_rate\Exchange_Rate_Report.xml"

    if os.path.exists(fpath):
        shutil.rmtree(fpath)

    print("download ....")
    IMFDriver().run()
    print("parse ....")
    finally_df = parse_imf_xml(fpath)
    collection = create_default_client().get_database("money").get_collection("usd")
    print("insert....")
    insert_new_rate_to_mongo(collection, finally_df)


class IMFDriver:
    def __init__(self):
        options = Options()
        options.add_experimental_option("prefs", {
            "download.default_directory": r"D:\imf_rate",
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        self.request_url = "https://www.imf.org/external/np/fin/ert/GUI/Pages/CountryDataBase.aspx"
        self.driver = webdriver.Chrome(options=options)

    def run(self):
        self.driver.get(self.request_url)
        self.step1()
        self.step2()
        self.step3()
        link_tag = self.driver.find_element_by_link_text("XML")
        link_tag.click()
        print("start to download....")
        time.sleep(60)
        self.driver.close()
        self.driver.quit()

    def step1(self):
        country = self.driver.find_element_by_id("ctl00_ContentPlaceHolder1_countryid")
        rate_type = self.driver.find_element_by_xpath("//input[@value='REP']")
        period = self.driver.find_element_by_id("ctl00_ContentPlaceHolder1_SelectPeriod")
        continue_button = self.driver.find_element_by_id("ctl00_ContentPlaceHolder1_BtnContinue")

        country.click()
        time.sleep(1)
        rate_type.send_keys(Keys.SPACE)
        time.sleep(1)
        # 构造select，并选择第二项
        select = Select(period)
        select.select_by_index(1)
        time.sleep(1)
        # submit
        continue_button.click()

    def step2(self):
        select_button = self.driver.find_element_by_id("ctl00_ContentPlaceHolder1_BtnSelect")
        select_button.click()
        time.sleep(1)
        continue_button = self.driver.find_element_by_id("ctl00_ContentPlaceHolder1_BtnContinueTwo")
        continue_button.click()

    def step3(self):
        continue_button = self.driver.find_element_by_id("ctl00_ContentPlaceHolder1_imgBtnPrepareReport")
        continue_button.click()


if __name__ == '__main__':
    run()
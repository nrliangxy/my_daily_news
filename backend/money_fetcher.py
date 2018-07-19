import pandas as pd
import datetime

from bson import ObjectId
from scrapy import Selector


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


if __name__ == '__main__':
    fpath = r"Exchange_Rate_Report.xml"
    finally_df = parse_imf_xml(fpath)

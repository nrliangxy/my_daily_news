import ast


class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self, source_code):
        self.source_code = source_code
        self._analysis_result = {}

    def visit_ClassDef(self, node):
        # 只提取第一个类
        if self._analysis_result.get("class"):
            return
        self._analysis_result.setdefault("class", node.name)
        # 遍历spider的类的属性和方法
        for n in ast.iter_child_nodes(node):
            if isinstance(n, ast.FunctionDef):
                self.append_class_function(n)
            # elif isinstance(n, ast.Assign):
            #     if not isinstance(n.value, ast.Str):
            #         continue
            #     for target in n.targets:
            #         if target.id == "name":
            #             self._analysis_result.update(
            #                 {"name": n.value.s}
            #             )
    def visit_Name(self, node):
        if node.id.upper() == node.id:
            self._analysis_result.setdefault("const", set()).add(node.id)

    def visit_FunctionDef(self, node):
        self._analysis_result.setdefault("functions", set()).add(node.name)

    def append_class_function(self, node):
        self._analysis_result.setdefault("functions", set()).add(node.name)

    def check_yield(self, node):
        """简单判断，有yield则认为是parse函数"""
        for n in ast.iter_child_nodes(node):
            if isinstance(n, ast.Yield):
                return True
            else:
                result = self.check_yield(n)
                if result:
                    return True
        return False

    def get_analysis_result(self):
        source_ast = ast.parse(self.source_code)
        self.visit(source_ast)
        return self._analysis_result


if __name__ == '__main__':
    x = CodeAnalyzer("""#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime
from health360.checker.base import BaseHealthCheck
import re
from health360.components.mutable import LengthBetween
from health360 import *
START_YEAR_DOWN_LEVEL = 2000
START_YEAR_UP_LEVEL = 2020
CAGR_UP_LEVEL = 2.5
END_YEAR_DOWN_LEVEL = 2016
END_YEAR_UP_LEVEL = 2031

CUT_START_LIST = ['other']
CUT_END_LIST = ['global', 'and', ' the', ' this']
BAD_NAME = ['european', 'asia pacific', 'united states', 'european union', 'worldwide', 'asia-pacific', 'the u.s.',
            'american', 'latin american', 'the world', 'display', 'hardware', 'software', 'growing']


class MarketingReportHealthCheck(BaseHealthCheck):
    MUST_REQUIRE_FIELD_SET = {"title", "source_url", "description", "published_ti", "categories", "report_code"}
    
    @classmethod
    def valid_source_url(cls, source_url, **kwargs):
        return 'http' in source_url
    
    @classmethod
    def valid_published_ti(cls, published_ti, **kwargs):
        post_time = datetime.datetime.utcfromtimestamp(kwargs['published_ts'])
        same_post = (
            post_time.year == published_ti["year"] and post_time.month == published_ti["month"] and post_time.day ==
            published_ti[
                "day"])
        return same_post
    
    @classmethod
    def valid_market_detail(cls, market_detail, **kwargs):
        r_list = []
        for item in market_detail:
            r = cls.market_detail_one(item)
            r_list.append(r)
        return all(r_list)
    
    @classmethod
    def valid_normalized_topic(cls, normalized_topic, **kwargs):
        categories = kwargs['categories']
        if str(normalized_topic) == str(categories):
            return False
        else:
            return True
    
    @classmethod
    def valid_description(cls, description, **kwargs):
        return LengthBetween(300).apply(description)

    @classmethod
    def filter_bad_title(cls, data):
        regex = r"(”)|(,)|(:)"
        start_sign = [True for i in CUT_START_LIST if data.startswith(i)]
        end_sign = [True for i in CUT_END_LIST if data.endswith(i)]
        if data in BAD_NAME:
            return False
        if len(start_sign) > 0 or len(end_sign) > 0:
            return False
        if len(data) < 5 and len(data) > 96:
            return False
        if data.encode('UTF-8').isdigit():
            return False
        if ChineseExists().apply(data):
            return False
        return not re.search(regex, data)
    
    @classmethod
    def market_detail_one(cls,item):
        start_year = item['start_year']
        end_year = item['end_year']
        cagr = item['cagr']
        start_valuation = item['start_valuation']
        end_valuation = item['end_valuation']
        market_name = item['market_name'].lower()
        check_year = cls.market_detail_year(start_year,end_year)
        check_cagr = cls.market_detail_cagr(cagr)
        check_valuation = cls.market_detail_valuation(start_valuation,end_valuation)
        check_market_name = cls.filter_bad_title(market_name)
        return check_year and check_cagr and check_valuation and check_market_name


    @classmethod
    def market_detail_cagr(cls,cagr):
        if float(cagr) > CAGR_UP_LEVEL:
            return False
        return True

    @classmethod
    def market_detail_valuation(cls,start_valuation,end_valutaion):
        if start_valuation > end_valutaion:
            return False
        return True

    @classmethod
    def market_detail_year(cls,start_year,end_year):
        if start_year < START_YEAR_DOWN_LEVEL and end_year > END_YEAR_UP_LEVEL:
            return False
        if start_year > end_year:
            return False
        return True


if __name__ == '__main__':
    print(MarketingReportHealthCheck.validate({
    "_id" : "f2ade63a-68af-11e8-aaf0-0242ac110002",
    "addresses" : [
        {
            "dict_id" : "LOCATION:170505"
        }
    ],
    "published_ts" : 1456790400,
    "description" : "This BCC Research report analyzes the advanced drug delivery market by technologies/systems, applications, routes of administration and drug delivery vehicles. Forecast given for the period 2015-2020. Use this report to: Identify the market dynamics of global advanced drug delivery technologies and their relevant business impact. Gain insight into the advanced drug delivery industry competitive landscape. Analyze the advanced drug delivery market by technology, application, routes of administration, and drug delivery vehicle. Gain information through patents on advanced drug delivery systems. Highlights The global advanced drug delivery market should grow from roughly $178.8 billion in 2015 to nearly $227.3 billion by 2020, with a compound annual growth rate (CAGR) of 4.9%. The North American market should grow from nearly $75.7 billion in 2015 to $93.4 billion by 2020, a CAGR of 4.3%. The European market should grow from roughly $57.3 billion in 2015 to nearly $72.1 billion by 2020, a CAGR of 4.7%. STUDY GOALS AND OBJECTIVES The study’s goal is to provide industry participants insights into the global advanced drug delivery technologies market, both in terms of quantitative and qualitative data, which could help them gain an understanding of the market to develop business/growth strategies, assess the landscape, analyze their current position and make more informed business decisions. In particular, the study’s objectives include the following: Provide comprehensive analysis of advanced drug delivery technologies, applications, routes of administration and drug delivery vehicles. Identify the market dynamics of each key market and the relevant business impact hereof. Offer market forecasting for four regions: North America, Europe, Asia and rest of the world (ROW). Report and analyze key market developments. Highlight and analyze market trends, drivers and restraints. Analyze each key region listed above. Analyze the market’s competitive landscape. REASONS FOR DOING THE STUDY Advances in medical science, research and development (R&D), and innovation are changing the dynamics of the life sciences industry, including biotechnology, pharmaceuticals and healthcare. The development of new drugs necessitates the development of different drug delivery systems, which is further driven by innovation in technology, R&D and scientific advancements. Advances in understanding human biology, diseases and medical treatments are opening new opportunities in the pharmaceutical industry. A drug delivery system is an important area where the need for better technologies for drug administration/delivery is in demand. A key driver of the growth in this industry is the advantages advanced drug delivery systems offer over traditional drug delivery systems, such as higher efficacy, localized treatment of diseases, duration of drug delivery, convenient routes of administration, better targeting and lower dosing frequency. For example, advanced drug delivery systems such as rectal drug delivery, lymphatic implants are more effective than traditional pharmaceuticals and promote better treatment outcomes (e.g., fewer side effects, continuous or extended release of the drug). Consequently, these developments are driving significant growth in the global drug delivery market. Currently, the global market for advanced drug delivery systems is valued at over $150 billion. This report offers an overview of current and future market characteristics of advanced drug delivery systems. It provides a comprehensive view of current and emerging drug delivery technologies, market drivers and restraints, the competitive landscape, and market revenues by technology across different regions (the United States, Europe, Asia and ROW).",
    "source" : "reportbuyer",
    "title" : "Global Markets and Technologies for Advanced Drug Delivery Systems",
    "source_url" : "https://www.reportbuyer.com/product/1940407/global-markets-and-technologies-for-advanced-drug-delivery-systems.html",
    "created_ts" : 1529412380,
    "categories" : [
        "Life Sciences",
        "Pharmaceutical"
    ],
    "data_status" : "ACTIVE",
    "published_ti" : {
        "month" : 3,
        "hour" : 0,
        "year" : 2016,
        "timezone" : None,
        "day" : 1,
        "quarter" : 1,
        "minute" : 0,
        "second" : 0
    },
    "report_code" : "1940407",
    "updated_ts" : 1530159532,
    "created_by" : "PIPELINE",
    "market_detail" : [
        {
            "start_valuation" : 178800000000.0,
            "end_valuation" : 227300000000.0,
            "start_year" : 2015.0,
            "cagr" : 0.049,
            "end_year" : 2020.0,
            "market_name" : "advanced drug delivery"
        }
    ],
    "normalized_country" : [
        {
            "dict_id" : "LOCATION:170505",
            "name" : "United States"
        }
    ],
    "source_unique" : "reportbuyer-1940407",
    "repo_id" : "f2ade63a-68af-11e8-aaf0-0242ac110002",
    "data_type" : "MARKETING_REPORT",
    "updated_by" : "handler_market_detail",
    "s3_key" : "raw_data/marketing_report/reportbuyer/45cfcab5da25491a63931c8726613cba.json",
    "event_name" : "MODIFY",
    "normalized_topic" : [
        "Globalism",
        "Periodicity",
        "Regionalism"
    ]
}))
""")
    print(x.get_analysis_result())
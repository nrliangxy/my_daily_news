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
    x = CodeAnalyzer("""class FundedHealthCheck(BaseHealthCheck):
    MUST_REQUIRE_FIELD_SET = {"title", "source_url", "funded_research_id", "source"}

    @classmethod
    def valid_title(cls, title, **kwargs):
        return Title.apply(title)

    @classmethod
    def valid_source_url(cls, source_url, **kwargs):
        return Link().apply(source_url)

    @classmethod
    def valid_description(cls, description, **kwargs):
        default_check = Content.apply(description)
        if not default_check:
            return False
        comp = ~WordExists("[unreadable]")
        return comp.apply(description)

    @classmethod
    def valid_amount(cls, amount, **kwargs):
        return Money.apply(amount)

    @classmethod
    def valid_close_ti(cls, close_ti, **kwargs):
        return (TimeBetween({"year": 1900}, {"year": 2100})
                & TimeBetween(kwargs.get("open_ti", close_ti))).apply(close_ti)

    @classmethod
    def valid_funded_research_id(cls, funded_research_id, **kwargs):
        source = kwargs.get("source")
        return WordStart(source+":").apply(funded_research_id)

class aaHealthCheck(BaseHealthCheck):
    MUST_REQUIRE_FIELD_SET = {"title", "source_url", "funded_research_id", "source"}

    @classmethod
    def valid_ti1le(cls, title, **kwargs):
        return Title.apply(title)

    @classmethod
    def valid_source_url(cls, source_url, **kwargs):
        return Link().apply(source_url)

    @classmethod
    def valid_description(cls, description, **kwargs):
        default_check = Content.apply(description)
        if not default_check:
            return False
        comp = ~WordExists("[unreadable]")
        return comp.apply(description)

    @classmethod
    def valid_amount(cls, amount, **kwargs):
        return Money.apply(amount)

    @classmethod
    def valid_close_ti(cls, close_ti, **kwargs):
        return (TimeBetween({"year": 1900}, {"year": 2100})
                & TimeBetween(kwargs.get("open_ti", close_ti))).apply(close_ti)

    @classmethod
    def valid_funded_research_id(cls, funded_research_id, **kwargs):
        source = kwargs.get("source")
        return WordStart(source+":").apply(funded_research_id)
        """)
    print(x.get_analysis_result())
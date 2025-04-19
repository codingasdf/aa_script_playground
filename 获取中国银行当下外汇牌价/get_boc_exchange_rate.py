"""
用于被quicker调用，获取html文件过程由quicker实现
"""


def extract_usd_exchange_rate(html_str):
    # 删除部分字符串，便于判断
    html_str = html_str.replace(' class="pjrq"', '')
    # 查找美元所在的行
    start_index = html_str.find('美元')  # 查找“美元”字符串在HTML中的位置
    if start_index == -1:
        return "没有找到美元的汇率数据。"  # 如果没有找到“美元”关键词，返回提示

    # 定位美元所在的 <tr> 标签的起始位置
    start_tr_index = html_str.rfind('<tr>', 0, start_index)  # 查找美元前面的 <tr> 标签
    end_tr_index = html_str.find('</tr>', start_index)  # 查找该行结束的位置

    # 截取包含美元数据的那一行
    usd_row = html_str[start_tr_index:end_tr_index]

    # 提取每个单元格的数据
    currency_name = extract_data_from_td(usd_row, 0)  # 货币名称
    buy_rate_hk = extract_data_from_td(usd_row, 1)  # 现汇买入价
    buy_rate_cash = extract_data_from_td(usd_row, 2)  # 现钞买入价
    sell_rate_hk = extract_data_from_td(usd_row, 3)  # 现汇卖出价
    sell_rate_cash = extract_data_from_td(usd_row, 4)  # 现钞卖出价
    bank_exchange_rate = extract_data_from_td(usd_row, 5)  # 中行折算价
    publish_date = extract_data_from_td(usd_row, 6)  # 发布日期
    publish_time = extract_data_from_td(usd_row, 7)  # 发布时间

    # 构造返回结果字符串
    result = (
        f"货币名称：{currency_name}\n"
        f"现汇买入价：{buy_rate_hk}\n"
        f"现钞买入价：{buy_rate_cash}\n"
        f"现汇卖出价：{sell_rate_hk}\n"
        f"现钞卖出价：{sell_rate_cash}\n"
        f"中行折算价：{bank_exchange_rate}\n"
        f"发布日期：{publish_date}\n"
        f"发布时间：{publish_time}"
    )

    return result


# 辅助函数，用于从 <td> 标签中提取数据
def extract_data_from_td(row, index):
    start_index = 0
    for _ in range(index + 1):
        start_index = row.find('<td>', start_index)
        start_index += len('<td>')  # 跳过 <td> 标签
    end_index = row.find('</td>', start_index)
    return row[start_index:end_index].strip()


# 输入html文本文件
html_content = """
https://www.boc.cn/sourcedb/whpj/index.html
也有可能在第二页
https://www.boc.cn/sourcedb/whpj/index_1.html
"""

# 调用函数，获取美元的汇率信息
usd_exchange_rate = extract_usd_exchange_rate(html_content)

# 输出结果
print(usd_exchange_rate)

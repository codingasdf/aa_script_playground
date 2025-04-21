import requests
import pandas as pd
from datetime import datetime
import re
import json


def get_zone_chart(zipcode_prefix, shipping_date=None):
    """
    获取指定邮编前缀和日期的分区表

    :param zipcode_prefix: 3位邮编前缀
    :param shipping_date: 日期，格式为 MM/DD/YYYY
    :return: 分区表数据
    """

    url = "https://postcalc.usps.com/DomesticZoneChart/GetZoneChart"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://postcalc.usps.com/DomesticZoneChart/',
        'Origin': 'https://postcalc.usps.com',
    }

    params = {
        "zipCode3Digit": zipcode_prefix,
        "shippingDate": shipping_date
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        # 尝试解析JSON
        try:
            return response.json()
        except json.JSONDecodeError:
            print("返回的不是有效的JSON数据")
            print("响应内容:", response.text)
            return None

    except requests.RequestException as e:
        print(f"获取分区表时发生错误: {e}")
        print("响应状态码:", e.response.status_code if hasattr(e, 'response') else "未知")
        print("响应内容:", e.response.text if hasattr(e, 'response') else "无")
        return None


def parse_zipcode_range(zipcode_range):
    """
    解析邮编范围字符串

    :param zipcode_range: 邮编范围字符串，如 '005---089'
    :return: 起始和结束邮编
    """
    # 处理类似 '005---089' 或 '500' 的情况，start_zipcode 补 0，end_zipcode 补 9
    parts = re.split(r'---|-', str(zipcode_range))
    if len(parts) == 1:
        return parts[0].ljust(5, "0"), parts[0].ljust(5, "9")
    else:
        return parts[0].ljust(5, "0"), parts[1].ljust(5, "9")


def extract_zone_data(zone_chart):
    """
    从分区表中提取分区数据

    :param zone_chart: 获取的分区表JSON数据
    :return: 分区数据列表
    """
    if not zone_chart:
        return []

    zone_data = []

    # 处理各列的邮编范围
    column_keys = ['Column0', 'Column1', 'Column2', 'Column3']
    for column_key in column_keys:
        if column_key in zone_chart:
            for entry in zone_chart[column_key]:
                start_zipcode, end_zipcode = parse_zipcode_range(entry['ZipCodes'])
                zone_data.append({
                    'start_zipcode': start_zipcode,
                    'end_zipcode': end_zipcode,
                    'zone': entry['Zone'],
                    'mail_service': entry['MailService']
                })

    # 处理5位邮编范围
    if 'Zip5Digit' in zone_chart:
        for entry in zone_chart['Zip5Digit']:
            start_zipcode, end_zipcode = parse_zipcode_range(entry['ZipCodes'])
            zone_data.append({
                'start_zipcode': start_zipcode,
                'end_zipcode': end_zipcode,
                'zone': entry['Zone'],
                'mail_service': entry['MailService']
            })

    return zone_data


def create_special_zones():
    """
    创建特殊分区列表

    :return: 特殊分区列表
    """
    special_zone_prefixes = [
        '006', '007', '008', '009', '090', '091', '092', '093', '094',
        '095', '096', '097', '098', '099', '340', '962', '963', '964',
        '965', '966', '967', '968', '969', '995', '996', '997', '998', '999'
    ]

    special_zones = []
    for prefix in special_zone_prefixes:
        special_zones.append({
            'start_zipcode': f'{prefix}00',
            'end_zipcode': f'{prefix}99',
            'zone': '9'
        })

    return special_zones


def process_zone_data(df):
    """
    对分区数据进行额外处理
    1. 去除mail_service列，去除zone列中的备注，去除重复列
    2. 处理邮编重复的情况，保留分区大的记录（展开邮编，对重复邮编保留zone更大的，排序，合并）

    :param df: 输入的DataFrame
    :return: 处理后的DataFrame
    """
    # 去除mail_service列
    df = df.drop(columns=['mail_service'])
    # 去除zone列中的备注
    df['zone'] = df['zone'].apply(lambda x: str(x).rstrip('+*'))
    # 去除重复列
    df = df.drop_duplicates()

    # 展开邮编
    expanded_data = []
    for _, row in df.iterrows():
        start = int(row['start_zipcode'])
        end = int(row['end_zipcode'])
        zone = row['zone']

        for zipcode in range(start, end + 1):
            expanded_data.append({
                'start_zipcode': f'{zipcode:05d}',
                'end_zipcode': f'{zipcode:05d}',
                'zone': zone
            })

    # 创建新的DataFrame
    expanded_df = pd.DataFrame(expanded_data)

    # 对于重复的邮编，保留zone更大的记录
    expanded_df = expanded_df.sort_values('zone', ascending=False).drop_duplicates(subset='start_zipcode', keep='first')

    # 对start_zipcode排序
    expanded_df = expanded_df.sort_values('start_zipcode')

    # 合并同分区的邮编
    merged_data = []
    current_group = None

    for _, row in expanded_df.iterrows():
        if current_group is None:
            current_group = {
                'start_zipcode': row['start_zipcode'],
                'end_zipcode': row['start_zipcode'],
                'zone': row['zone']
            }
        else:
            # 如果是同一个分区，更新end_zipcode
            if (row['zone'] == current_group['zone'] and
                    int(row['start_zipcode']) == int(current_group['end_zipcode']) + 1):
                current_group['end_zipcode'] = row['end_zipcode']
            else:
                # 保存当前分组，开始新的分组
                merged_data.append(current_group)
                current_group = {
                    'start_zipcode': row['start_zipcode'],
                    'end_zipcode': row['start_zipcode'],
                    'zone': row['zone']
                }

    # 添加最后一个分组
    if current_group:
        merged_data.append(current_group)

    # 创建最终的DataFrame
    result_df = pd.DataFrame(merged_data)

    return result_df


def main():
    # 输入3位发件邮编
    zipcode_prefix = input("请输入发件地区邮编前3位: ")

    # 输入日期，直接回车使用当前日期
    shipping_date_input = input("请输入日期，格式MMDDYYYY，直接回车使用系统当前日期）: ")
    # 格式化日期，传入参数中"%2F"为斜杠"/"，转换格式为MM/DD/YYYY
    if shipping_date_input:
        shipping_date = f"{shipping_date_input[:2]}/{shipping_date_input[2:4]}/{shipping_date_input[4:]}"
    else:
        shipping_date = datetime.now().strftime("%m/%d/%Y")

    # 询问是否加入特殊分区
    add_special_zones = input("是否加入特殊分区（非大陆等算最远区）？\n1，加入（回车默认） 2，不加入\n")
    # 询问是否处理数据
    process_data = input("是否对分区数据进行额外处理（去重排序合并）？\n1，处理（回车默认） 2，不处理\n")

    # 获取分区表
    zone_chart = get_zone_chart(zipcode_prefix, shipping_date)

    if zone_chart:
        # 提取分区数据
        zone_data = extract_zone_data(zone_chart)

        if zone_data:
            # 创建DataFrame
            df = pd.DataFrame(zone_data)

            # 根据用户选择处理添加特殊分区
            if add_special_zones == '' or add_special_zones == '1':
                special_zones_df = pd.DataFrame(create_special_zones())
                df = pd.concat([df, special_zones_df], ignore_index=True)

            # 根据用户选择处理数据
            if process_data == '' or process_data == '1':
                df = process_zone_data(df)

            # 保存到Excel
            output_filename = f"zone_chart_{zipcode_prefix}_{shipping_date.replace('/', '-')}.xlsx"
            df.to_excel(output_filename, index=False)

            print(f"分区表已保存到 {output_filename}")
            print(df)
        else:
            print("未能提取到有效的分区数据")
    else:
        print("无法获取分区表")


if __name__ == "__main__":
    main()
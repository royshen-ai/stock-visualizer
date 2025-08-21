import pandas as pd
import re
import numpy as np

# 读取CSV文件，跳过表头行
# 使用明确的列索引提取所需数据(A列、D列、E列、H列)
df = pd.read_csv('transaction.csv', header=None, skiprows=1, encoding='gbk', usecols=[0, 3, 4, 7])

# 设置列名
df.columns = ['日期', '股票代码', '买卖类型', '成交价']

# 转换股票代码格式（去除后缀如.XSHE或.XSHG）
df['股票代码'] = df['股票代码'].str.extract(r'(\d+)\.')[0]

# 转换日期格式为YYYYMMDD
df['日期'] = pd.to_datetime(df['日期'], errors='coerce').dt.strftime('%Y%m%d')

# 将买卖类型转换为数字编码(买=1,卖=2)
df['买卖类型'] = df['买卖类型'].apply(lambda x: 1 if str(x).strip() in ['买', 'B'] else 2)

# 处理成交价(去除非数字字符、替换空字符串为NaN并转换为浮点数)
df['成交价'] = df['成交价'].replace(r'[^\d.]', '', regex=True)
df['成交价'] = df['成交价'].replace('', np.nan)
df['成交价'] = pd.to_numeric(df['成交价'], errors='coerce')

# 过滤无效数据
df = df.dropna()

# 保存为通达信要求的ANSI编码(gbk)CSV文件
df.to_csv('tdx_transaction_new.csv', index=False, encoding='gbk')
print('转换完成，生成文件: tdx_transaction_new.csv')
import pandas as pd
import numpy as np
import re
from datetime import datetime

# 读取Excel文件
# 使用工作目录中的position11.xlsx
excel_path = 'position11.xlsx'

def generate_trade_report():
    try:
        # 使用pandas读取Excel文件
        df = pd.read_excel(excel_path, engine='openpyxl')
        
        # 清理列名（去除所有空格和特殊字符）
        # 完整的列名预处理流程
        df.columns = df.columns.str.strip()
        df.columns = df.columns.str.replace('\s+', '', regex=True)
        df.columns = df.columns.str.replace('[^a-zA-Z0-9_\u4e00-\u9fa5]', '', regex=True)
        print(f"清理后的列名: {', '.join(df.columns)}")
        # 详细打印每一列以确认清理效果
        for col in df.columns:
            print(f"- 列名: '{col}'")
        
        # 检查并修复开仓日期列名
        if '开仓日期' not in df.columns:
            # 尝试查找包含开仓/建仓/买入等关键词的日期列
            date_columns = [col for col in df.columns if any(keyword in col for keyword in ['开仓', '建仓', '买入'])]
            if date_columns:
                df.rename(columns={date_columns[0]: '开仓日期'}, inplace=True)
            else:
                raise ValueError(f"Excel文件中未找到开仓日期相关列。可用列: {', '.join(df.columns)}")
        
        # 直接使用持仓均价期货列作为开仓均价
        # 查找简化后的价格列（用户已删除持仓均价列）
        # 查找开仓价相关列（用户可能已将'开仓均价'简化为'开仓价'）
        # 直接查找'开仓均价'列
        # 使用收盘价作为替代数据源
        # 已在数据加载后统一处理列名清理
        # df.columns = df.columns.str.strip()
        
        # 优先查找精确列名，再尝试其他可能的列名
        price_columns = []
        if '开仓均价' in df.columns:
            price_columns = ['开仓均价']
        elif '开仓价' in df.columns:
            price_columns = ['开仓价']
        # 若未找到，保留原收盘价作为最后的备选
        elif '收盘价' in df.columns:
            price_columns = ['收盘价']
        elif '收盘价结算价' in df.columns:
            price_columns = ['收盘价结算价']
        if price_columns:
            original_price_col = price_columns[0]
            print(f"使用'{original_price_col}'作为开仓均价数据源")
            # 预处理价格列，处理中文数字和特殊格式
            # 打印原始数据进行调试
            # 打印更多原始数据样本和数据类型
            print(f"'{original_price_col}'数据类型: {df[original_price_col].dtype}")
            print(f"'{original_price_col}'原始数据前20行: {df[original_price_col].head(20).tolist()}")
            print(f"'{original_price_col}'唯一值: {df[original_price_col].unique().tolist()}")
            
            # 创建中文数字到阿拉伯数字的映射
            chinese_num_map = {'零':0, '一':1, '二':2, '三':3, '四':4, '五':5, '六':6, '七':7, '八':8, '九':9, '十':10}
            
            # 函数：转换中文数字和混合格式到浮点数
            def convert_chinese_price(price_str):
                if pd.isna(price_str):
                    return np.nan
                if isinstance(price_str, (int, float)):
                    return price_str
                # 更激进的清理策略 - 只保留数字和小数点
                cleaned = re.sub(r'[^0-9.]', '', str(price_str))
                if not cleaned:
                    return np.nan
                # 尝试直接转换
                try:
                    return float(cleaned)
                except ValueError:
                    # 简单中文数字转换逻辑
                    try:
                        return sum(chinese_num_map[char] for char in cleaned if char in chinese_num_map)
                    except:
                        return np.nan
            
            # 应用转换函数
            df['开仓均价'] = df[original_price_col].apply(convert_chinese_price)
            df['开仓均价'] = pd.to_numeric(df['开仓均价'], errors='coerce')
            print(f"'{original_price_col}'预处理后样本数据: {df['开仓均价'].head(5).tolist()}")
        else:
            raise ValueError(f"未找到包含'均价'的列。可用列: {', '.join(df.columns)}")

        # 预处理价格列，处理中文数字和特殊格式
        # 打印原始数据进行调试
        # 打印更多原始数据样本和数据类型
        print(f"'{original_price_col}'数据类型: {df[original_price_col].dtype}")
        print(f"'{original_price_col}'原始数据前20行: {df[original_price_col].head(20).tolist()}")
        print(f"'{original_price_col}'唯一值: {df[original_price_col].unique().tolist()}")
        
        # 创建中文数字到阿拉伯数字的映射
        chinese_num_map = {'零':0, '一':1, '二':2, '三':3, '四':4, '五':5, '六':6, '七':7, '八':8, '九':9, '十':10}
        
        # 函数：转换中文数字和混合格式到浮点数
        def convert_chinese_price(price_str):
                if pd.isna(price_str):
                    return np.nan
                if isinstance(price_str, (int, float)):
                    return price_str
                # 更激进的清理策略 - 只保留数字和小数点
                cleaned = re.sub(r'[^0-9.]', '', str(price_str))
                if not cleaned:
                    return np.nan
                # 尝试直接转换
                try:
                    return float(cleaned)
                except ValueError:
                    # 简单中文数字转换逻辑
                    try:
                        return sum(chinese_num_map[char] for char in cleaned if char in chinese_num_map)
                    except:
                        return np.nan
            

        
        # 查找简化后的盈亏列
        profit_columns = [col for col in df.columns if '盈亏' in col]
        if not profit_columns:
            raise ValueError(f"未找到盈亏相关列。可用列: {', '.join(df.columns)}")
        profit_col = profit_columns[0]
        print(f"使用'{profit_col}'作为盈亏相关列")
        
        # 强制使用可用数量作为数量列
        if '可用数量' in df.columns:
            # 打印可用数量原始数据
            print(f"可用数量原始样本数据: {df['可用数量'].head(5).tolist()}")
            # 预处理可用数量列
            df['可用数量'] = df['可用数量'].replace(['-', ' ', ''], np.nan)
            print(f"可用数量预处理后样本数据: {df['可用数量'].head(5).tolist()}")
            if '数量' in df.columns:
                print("将原数量列重命名为数量_old")
                df.rename(columns={'数量': '数量_old'}, inplace=True)
            df.rename(columns={'可用数量': '数量'}, inplace=True)
            print("已将'可用数量'重命名为'数量'")
        
        # 处理数量列非数值数据
        if '数量' in df.columns:
            # 移除所有非数字字符
            df['数量'] = df['数量'].replace(r'[^0-9]', '', regex=True)
            df['数量'] = df['数量'].replace(['-', ' ', ''], np.nan)
            print(f"数量列预处理后样本数据: {df['数量'].head(5).tolist()}")
        
        # 数据类型转换
        # 处理开仓均价中的非数值字符
        if '开仓均价' in df.columns:
            # 将非数值字符替换为空
            df['开仓均价'] = df['开仓均价'].replace(['-', ' ', ''], np.nan)
            print(f"开仓均价原始样本数据: {df['开仓均价'].head(5).tolist()}")
            df['开仓均价'] = pd.to_numeric(df['开仓均价'], errors='coerce')
        
        # 使用动态确定的价格列
        original_price_col = price_columns[0]
        print(f"{original_price_col}原始样本数据: {df[original_price_col].head(5).tolist()}")
        # 预处理价格列 - 移除所有非数字字符
        df[original_price_col] = df[original_price_col].replace(r'[^0-9.]', '', regex=True)
        df[original_price_col] = df[original_price_col].replace(['-', ' ', ''], np.nan)
        print(f"{original_price_col}预处理后样本数据: {df[original_price_col].head(5).tolist()}")
        df['开仓均价'] = pd.to_numeric(df[original_price_col], errors='coerce')
        print(f"使用{original_price_col}后样本数据: {df['开仓均价'].head(5).tolist()}")
        # 使用动态价格列进行数值转换
        df[original_price_col] = pd.to_numeric(df[original_price_col], errors='coerce')
        df['数量'] = pd.to_numeric(df['数量'], errors='coerce', downcast='integer')
        
        # 检查转换后的数据质量
        print(f"开仓均价非空且有效记录数: {df['开仓均价'].notna().sum()}")
        # 打印开仓均价样本数据以检查问题
        print(f"开仓均价样本数据: {df['开仓均价'].head(5).tolist()}")
        print(f"{original_price_col}非空且有效记录数: {df[original_price_col].notna().sum()}")
        print(f"盈亏逐笔浮盈非空且有效记录数: {df['盈亏逐笔浮盈'].notna().sum()}")
        
        # 数据清洗
        # 过滤掉空值和非股票数据
        # 调试打印原始数据量
        print(f"原始数据记录数: {len(df)}")
        
        # 数据清洗
        # 过滤掉空值和非股票数据
        # 统计各列非空值数量
        print(f"品种非空记录数: {df['品种'].notna().sum()}")
        print(f"数量非空记录数: {df['数量'].notna().sum()}")
        print(f"开仓均价非空记录数: {df['开仓均价'].notna().sum()}")
        print(f"{original_price_col}非空记录数: {df[original_price_col].notna().sum()}")
        print(f"盈亏逐笔浮盈非空记录数: {df['盈亏逐笔浮盈'].notna().sum()}")
        
        # 放宽空值过滤条件，只检查必要列
        df = df[df['品种'].notna() & df['数量'].notna() & df['开仓均价'].notna()]
        print(f"空值过滤后记录数: {len(df)}")
        
        # 调整数量过滤条件，允许等于0的情况# 过滤掉无效数值
        df = df[df['数量'] >= 0]  # 考虑有持仓和平仓的记录
        print(f"数量过滤后记录数: {len(df)}")
        
        # 临时移除开仓均价过滤以检查数据
        print("临时移除开仓均价过滤以检查数据完整性")
        
        # 临时完全移除价格过滤以便调试
        print("临时完全移除价格过滤以便调试")
        # df = df[(df['开仓均价'] >= 0) & (df['开仓均价'].notna())]
        # print(f"价格过滤后记录数: {len(df)}")
        
        # 检查当前数据情况
        print(f"开仓均价非空记录数: {df['开仓均价'].notna().sum()}")
        print(f"开仓均价大于0记录数: {(df['开仓均价'] > 0).sum()}")
        
        # 确保日期列格式正确
        # 验证开仓日期列是否存在
        if '开仓日期' not in df.columns:
            raise ValueError(f"转换日期前未找到'开仓日期'列。当前列: {', '.join(df.columns)}")
        
        df['日期'] = pd.to_datetime(df['日期'])
        df['开仓日期'] = pd.to_datetime(df['开仓日期'])
        print("日期列转换成功")
        
        # 过滤掉无效数值
        df = df[df['开仓均价'] > 0]
        
        # 按股票和开仓日期分组，识别每笔交易
        trades = []
        grouped = df.groupby(['品种', '开仓日期'])
        
        for (stock, open_date), group in grouped:
            # 获取该笔交易的所有记录
            trade_records = group.sort_values('日期')
            
            # 买入信息
            buy_date = open_date
            buy_price = trade_records.iloc[0]['开仓均价']
            quantity = trade_records.iloc[0]['数量']
            
            # 卖出信息（最后一条记录的日期和收盘价）
            sell_date = trade_records.iloc[-1]['日期']
            # 使用动态确定的价格列获取卖出价格
            sell_price = trade_records.iloc[-1][original_price_col]
            
            # 计算盈亏
            profit_amount = trade_records.iloc[-1][profit_col]
            
            # 验证盈亏金额是否有效
            if pd.isna(profit_amount):
                print(f"警告: 股票{stock}在{open_date}的盈亏金额为空，跳过该笔交易")
                continue
            
            if buy_price > 0:
                profit_percent = (profit_amount / (buy_price * quantity)) * 100
            else:
                profit_percent = 0
            
            # 确保数值有效
            profit_amount = float(round(profit_amount, 2))
            profit_percent = float(round(profit_percent, 2))
            
            # 添加到交易列表
            trades.append({
                '股票名称': stock,
                '买入日期': buy_date.strftime('%Y-%m-%d'),
                '买入价格': float(round(buy_price, 2)),
                '卖出日期': sell_date.strftime('%Y-%m-%d'),
                '卖出价格': float(round(sell_price, 2)),
                '数量': int(quantity),
                '盈亏金额': profit_amount,
                '盈亏百分比': profit_percent
            })
        
        # 检查交易列表是否为空
        if not trades:
            raise ValueError("未找到有效的交易记录，请检查数据或过滤条件")
        
        # 创建结果DataFrame并按盈亏百分比排序
        result_df = pd.DataFrame(trades)
        
        # 确保数值列类型正确
        result_df['盈亏金额'] = pd.to_numeric(result_df['盈亏金额'], errors='coerce').astype(float)
        result_df['盈亏百分比'] = pd.to_numeric(result_df['盈亏百分比'], errors='coerce').astype(float)
        result_df = result_df.dropna(subset=['盈亏金额', '盈亏百分比'])
        
        # 再次检查是否有有效数据
        if result_df.empty:
            raise ValueError("所有交易记录均包含无效的盈亏数据")
        
        result_df = result_df.sort_values('盈亏百分比', ascending=False)
        
        # 生成HTML报告
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>股票交易盈亏报告</title>
    <style>
            body {{
                font-family: 'Arial', sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            h1 {{
                color: #333;
                text-align: center;
                margin-bottom: 30px;
            }}
            .report-container {{
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            .report-meta {{
                color: #666;
                text-align: right;
                margin-bottom: 20px;
                font-style: italic;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }}
            tr:hover {{
                background-color: #f9f9f9;
            }}
            .positive {{
                color: #4CAF50;
                font-weight: bold;
            }}
            .negative {{
                color: #F44336;
                font-weight: bold;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }}
            .filter-container {{
                margin-bottom: 20px;
            }}
            input[type="text"] {{
                padding: 8px;
                width: 300px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
        </style>
</head>
<body>
    <div class="report-container">
        <div class="header">
            <h1>股票交易盈亏报告</h1>
        </div>
        <div class="report-meta">
            生成日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        <div class="filter-container">
            <input type="text" id="searchInput" placeholder="搜索股票名称..." onkeyup="searchTable()">
        </div>
        {result_df.to_html(index=False, classes='trade-table', justify='left',
                          formatters={{
                              '盈亏金额': lambda x: f'<span class="positive">{{x}}</span>' if float(x) > 0 else f'<span class="negative">{{x}}</span>',
                              '盈亏百分比': lambda x: f'<span class="positive">{{x}}%</span>' if float(x) > 0 else f'<span class="negative">{{x}}%</span>'
                          }})}
    </div>

    <script>
        // 搜索功能
        function searchTable() {{
            const input = document.getElementById('searchInput');
            const filter = input.value.toUpperCase();
            const table = document.querySelector('.trade-table');
            const tr = table.getElementsByTagName('tr');

            for (let i = 1; i < tr.length; i++) {{
                const td = tr[i].getElementsByTagName('td')[0];
                if (td) {{
                    const txtValue = td.textContent || td.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {{
                        tr[i].style.display = '';
                    }} else {{
                        tr[i].style.display = 'none';
                    }}
                }}
            }}
        }}
    </script>
</body>
</html>
        """
        
        # 保存HTML文件到当前工作目录
        with open('stock_trades.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(r"交易报告已生成: c:\Users\X1 Yoga\Saved Games\AIcode\stock_trades.html")
        return True
        
    except Exception as e:
        print(f"生成报告时出错: {str(e)}")
        return False

# 执行报告生成
if __name__ == "__main__":
    generate_trade_report()
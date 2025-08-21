import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import random
import requests
import json
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta
import numpy as np

class SimpleStockVisualizer:
    def __init__(self):
        self.transactions = None
        
    def load_transactions(self, file_path):
        """加载交易数据"""
        try:
            # 尝试不同的编码方式
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
            
            for encoding in encodings:
                try:
                    if 'new' in file_path:
                        # 包含价格的文件
                        df = pd.read_csv(file_path, encoding=encoding, header=None, 
                                       names=['date', 'stock_code', 'direction', 'price'])
                    else:
                        # 不包含价格的文件
                        df = pd.read_csv(file_path, encoding=encoding, header=None,
                                       names=['date', 'stock_code', 'direction'])
                        df['price'] = None
                    break
                except UnicodeDecodeError:
                    continue
            else:
                print("无法读取文件，请检查文件编码")
                return False
                
            # 数据处理
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            # 确保股票代码保持为字符串格式，避免前导零被截断
            df['stock_code'] = df['stock_code'].astype(str).str.zfill(6)
            df['action'] = df['direction'].map({1: '买入', 2: '卖出'})
            
            self.transactions = df
            print(f"成功加载 {len(df)} 条交易记录")
            return True
            
        except Exception as e:
            print(f"加载文件时出错: {str(e)}")
            return False
    
    def get_stock_data_eastmoney(self, stock_code, start_date=None, end_date=None):
        """
        使用东方财富免费接口获取股票K线数据
        """
        try:
            # 确保stock_code是字符串
            stock_code = str(stock_code)
            
            # 处理股票代码格式
            if stock_code.startswith('6'):
                # 上海股票
                market_code = f"1.{stock_code}"
            elif stock_code.startswith('0') or stock_code.startswith('3'):
                # 深圳股票
                market_code = f"0.{stock_code}"
            else:
                market_code = stock_code
            
            # 东方财富K线数据接口
            url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                'secid': market_code,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': '101',  # 日K线
                'fqt': '1',    # 前复权
                'beg': '0',
                'end': '20500000'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'http://quote.eastmoney.com/',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }
            
            print(f"正在从东方财富获取股票 {stock_code} 的数据...")
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if data.get('data') and data['data'].get('klines'):
                        klines = data['data']['klines']
                        
                        if not klines:
                            print(f"东方财富返回空数据，股票代码 {stock_code} 可能不存在")
                            return None
                        
                        # 解析K线数据
                        df_data = []
                        for line in klines:
                            try:
                                parts = line.split(',')
                                if len(parts) >= 6:
                                    df_data.append({
                                        'Date': pd.to_datetime(parts[0]),
                                        'Open': float(parts[1]),
                                        'Close': float(parts[2]),
                                        'High': float(parts[3]),
                                        'Low': float(parts[4]),
                                        'Volume': int(parts[5])
                                    })
                            except (ValueError, IndexError):
                                continue  # 跳过无效数据行
                        
                        if df_data:
                            df = pd.DataFrame(df_data)
                            df.set_index('Date', inplace=True)
                            
                            # 过滤日期范围
                            if start_date:
                                start_dt = pd.to_datetime(start_date)
                                df = df[df.index >= start_dt]
                            if end_date:
                                end_dt = pd.to_datetime(end_date)
                                df = df[df.index <= end_dt]
                            
                            print(f"✅ 东方财富接口成功获取 {len(df)} 条K线数据")
                            return df
                        else:
                            print("东方财富数据解析失败，数据格式可能有问题")
                    else:
                        print("东方财富接口返回数据格式异常")
                        
                except json.JSONDecodeError as e:
                    print(f"东方财富接口返回数据解析失败: {str(e)}")
            else:
                print(f"东方财富接口请求失败，状态码: {response.status_code}")
            
            return None
            
        except requests.exceptions.Timeout:
            print("东方财富接口请求超时")
            return None
        except requests.exceptions.ConnectionError:
            print("东方财富接口连接失败")
            return None
        except Exception as e:
            print(f"东方财富接口异常: {str(e)}")
            return None
    
    def get_stock_data_yahoo(self, stock_code, start_date, end_date, max_retries=3):
        """使用Yahoo Finance获取股票K线数据（备用方案）"""
        # 确保股票代码是字符串类型
        stock_code = str(stock_code)
        
        # 转换股票代码格式
        if stock_code.startswith('6'):
            symbol = f"{stock_code}.SS"  # 上海交易所
        elif stock_code.startswith(('0', '3')):
            symbol = f"{stock_code}.SZ"  # 深圳交易所
        else:
            symbol = stock_code
        
        print(f"正在获取股票 {stock_code} 的数据...")
        
        for attempt in range(max_retries):
            try:
                # 添加随机延迟以避免频率限制
                if attempt > 0:
                    delay = random.uniform(2, 5) * (attempt + 1)
                    print(f"正在重试获取股票数据，等待 {delay:.1f} 秒...")
                    time.sleep(delay)
                
                # 获取股票数据
                stock = yf.Ticker(symbol)
                data = stock.history(start=start_date, end=end_date)
                
                if data.empty:
                    print(f"无法获取股票 {stock_code} 的数据，可能该股票不存在或已退市")
                    return None
                    
                return data
                
            except Exception as e:
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "too many requests" in error_msg:
                    if attempt < max_retries - 1:
                        print(f"API频率限制，正在重试... (尝试 {attempt + 1}/{max_retries})")
                        continue
                    else:
                        print("API频率限制，请稍后再试。建议：")
                        print("1. 等待几分钟后重试")
                        print("2. 或者尝试查看其他股票")
                        return None
                else:
                    print(f"获取股票数据时出错: {str(e)}")
                    return None
        
        return None
    
    def get_stock_data_tencent(self, stock_code, start_date=None, end_date=None):
        """
        使用腾讯股票接口获取实时数据（备用方案）
        """
        try:
            # 确保stock_code是字符串
            stock_code = str(stock_code)
            
            # 处理股票代码格式
            if stock_code.startswith('6'):
                tencent_code = f"sh{stock_code}"
            elif stock_code.startswith('0') or stock_code.startswith('3'):
                tencent_code = f"sz{stock_code}"
            else:
                tencent_code = stock_code
            
            # 腾讯股票接口
            url = f"http://qt.gtimg.cn/q={tencent_code}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'http://qt.gtimg.cn/'
            }
            
            print(f"正在从腾讯接口获取股票 {stock_code} 的数据...")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text.strip()
                
                if content and '~' in content:
                    # 解析腾讯接口返回的数据
                    try:
                        # 提取数据部分
                        data_part = content.split('="')[1].rstrip('";')
                        fields = data_part.split('~')
                        
                        if len(fields) >= 6:
                            # 创建简单的当日数据
                            current_price = float(fields[3]) if fields[3] else 0
                            prev_close = float(fields[4]) if fields[4] else current_price
                            
                            # 由于腾讯接口主要提供实时数据，我们创建一个简单的DataFrame
                            today = datetime.now().strftime('%Y-%m-%d')
                            df_data = [{
                                'Date': pd.to_datetime(today),
                                'Open': prev_close,
                                'High': current_price,
                                'Low': current_price,
                                'Close': current_price,
                                'Volume': 0
                            }]
                            
                            df = pd.DataFrame(df_data)
                            df.set_index('Date', inplace=True)
                            
                            print(f"✅ 腾讯接口获取到实时数据")
                            return df
                    except (ValueError, IndexError) as e:
                        print(f"腾讯接口数据解析失败: {str(e)}")
                else:
                    print("腾讯接口返回数据格式异常")
            else:
                print(f"腾讯接口请求失败，状态码: {response.status_code}")
            
            return None
            
        except Exception as e:
            print(f"腾讯接口异常: {str(e)}")
            return None
    
    def get_stock_data(self, stock_code, start_date, end_date, max_retries=3):
        """
        获取股票K线数据 - 优先使用国内数据源
        """
        # 首先尝试东方财富接口
        data = self.get_stock_data_eastmoney(stock_code, start_date, end_date)
        if data is not None and not data.empty:
            return data
        
        # 如果失败，尝试腾讯接口
        print("东方财富接口获取失败，尝试腾讯接口...")
        data = self.get_stock_data_tencent(stock_code, start_date, end_date)
        if data is not None and not data.empty:
            return data
        
        # 最后尝试Yahoo Finance
        print("腾讯接口也失败，尝试Yahoo Finance...")
        return self.get_stock_data_yahoo(stock_code, start_date, end_date, max_retries)
    
    def plot_stock_with_trades(self, stock_code, save_plot=False):
        """绘制带交易标记的K线图"""
        if self.transactions is None:
            print("请先加载交易数据")
            return
        
        # 筛选该股票的交易记录
        stock_trades = self.transactions[self.transactions['stock_code'] == stock_code].copy()
        
        if stock_trades.empty:
            print(f"没有找到股票 {stock_code} 的交易记录")
            return
        
        # 确定日期范围
        start_date = stock_trades['date'].min() - timedelta(days=30)
        end_date = stock_trades['date'].max() + timedelta(days=30)
        
        # 获取股票数据
        stock_data = self.get_stock_data(stock_code, start_date, end_date)
        
        if stock_data is None:
            return
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 创建子图 - K线图和成交量图
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), 
                                      gridspec_kw={'height_ratios': [4, 1]}, 
                                      sharex=True)
        
        # 绘制K线图（使用candlestick风格）
        from matplotlib.patches import Rectangle
        
        for i, (date, row) in enumerate(stock_data.iterrows()):
            open_price = row['Open']
            close_price = row['Close']
            high_price = row['High']
            low_price = row['Low']
            
            # 判断涨跌，设置颜色 - 红涨绿跌
            if close_price >= open_price:
                color = 'red'  # 上涨为红色
                body_color = 'red'
            else:
                color = 'green'  # 下跌为绿色
                body_color = 'green'
            
            # 绘制影线
            ax1.plot([date, date], [low_price, high_price], color=color, linewidth=1)
            
            # 绘制实体
            body_height = abs(close_price - open_price)
            body_bottom = min(open_price, close_price)
            
            if body_height > 0:
                rect = Rectangle((date, body_bottom), 0, body_height, 
                               facecolor=body_color, edgecolor=color, alpha=0.8)
                ax1.add_patch(rect)
            else:
                # 十字星
                ax1.plot([date, date], [open_price, close_price], color=color, linewidth=2)
        
        # 绘制成交量
        if 'Volume' in stock_data.columns:
            volume_colors = []
            for i, (date, row) in enumerate(stock_data.iterrows()):
                if row['Close'] >= row['Open']:
                    volume_colors.append('red')  # 上涨日成交量为红色
                else:
                    volume_colors.append('green')  # 下跌日成交量为绿色
            
            ax2.bar(stock_data.index, stock_data['Volume'], 
                   color=volume_colors, alpha=0.7, width=1)
            ax2.set_ylabel('成交量', fontsize=12)
            ax2.grid(True, alpha=0.3)
        
        # 添加交易标记
        buy_trades = stock_trades[stock_trades['direction'] == 1]
        sell_trades = stock_trades[stock_trades['direction'] == 2]
        
        # 买入标记
        if not buy_trades.empty:
            buy_prices = []
            buy_dates = []
            for _, trade in buy_trades.iterrows():
                trade_date = trade['date']
                # 找到最接近的交易日价格
                closest_data = stock_data[stock_data.index >= trade_date]
                if not closest_data.empty:
                    price = trade['price'] if pd.notna(trade['price']) else closest_data.iloc[0]['Close']
                    buy_prices.append(price)
                    buy_dates.append(trade_date)
            
            if buy_prices:
                ax1.scatter(buy_dates, buy_prices, marker='^', s=100, color='red', 
                          label='买入', zorder=5)
        
        # 卖出标记
        if not sell_trades.empty:
            sell_prices = []
            sell_dates = []
            for _, trade in sell_trades.iterrows():
                trade_date = trade['date']
                # 找到最接近的交易日价格
                closest_data = stock_data[stock_data.index >= trade_date]
                if not closest_data.empty:
                    price = trade['price'] if pd.notna(trade['price']) else closest_data.iloc[0]['Close']
                    sell_prices.append(price)
                    sell_dates.append(trade_date)
            
            if sell_prices:
                ax1.scatter(sell_dates, sell_prices, marker='v', s=100, color='green', 
                          label='卖出', zorder=5)
        
        # 设置图表格式
        ax1.set_title(f'股票 {stock_code} K线图及交易记录', fontsize=16, fontweight='bold')
        ax1.set_ylabel('价格 (元)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 设置x轴格式（只在底部子图）
        ax2.set_xlabel('日期', fontsize=12)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator())
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        if save_plot:
            plt.savefig(f'stock_{stock_code}_chart.png', dpi=300, bbox_inches='tight')
            print(f"图表已保存为 stock_{stock_code}_chart.png")
        
        plt.show()
        
        # 打印交易统计
        print(f"\n股票 {stock_code} 交易统计:")
        print(f"总交易次数: {len(stock_trades)}")
        print(f"买入次数: {len(buy_trades)}")
        print(f"卖出次数: {len(sell_trades)}")
        
        # 显示交易明细
        print("\n交易明细:")
        for _, trade in stock_trades.iterrows():
            price_info = f", 价格: {trade['price']:.2f}" if pd.notna(trade['price']) else ""
            print(f"{trade['date'].strftime('%Y-%m-%d')}: {trade['action']}{price_info}")
    
    def show_all_stocks(self):
        """显示所有股票的交易概览"""
        if self.transactions is None:
            print("请先加载交易数据")
            return
        
        stock_codes = sorted(self.transactions['stock_code'].unique())
        
        print("\n所有股票交易概览:")
        print("-" * 80)
        print(f"{'股票代码':<10} {'总交易次数':<10} {'买入次数':<10} {'卖出次数':<10} {'首次交易':<12} {'最后交易':<12}")
        print("-" * 80)
        
        for stock in stock_codes:
            stock_trades = self.transactions[self.transactions['stock_code'] == stock]
            buy_count = len(stock_trades[stock_trades['direction'] == 1])
            sell_count = len(stock_trades[stock_trades['direction'] == 2])
            
            print(f"{stock:<10} {len(stock_trades):<10} {buy_count:<10} {sell_count:<10} "
                  f"{stock_trades['date'].min().strftime('%Y-%m-%d'):<12} "
                  f"{stock_trades['date'].max().strftime('%Y-%m-%d'):<12}")
        
        return stock_codes

def main():
    print("=" * 60)
    print("           股票交易可视化工具")
    print("=" * 60)
    
    visualizer = SimpleStockVisualizer()
    
    # 加载数据
    print("\n1. 加载交易数据")
    file_path = input("请输入CSV文件路径 (直接回车使用默认文件 tdx_transaction_new.csv): ").strip()
    
    if not file_path:
        file_path = "tdx_transaction_new.csv"
    
    if not visualizer.load_transactions(file_path):
        return
    
    while True:
        print("\n" + "="*50)
        print("请选择操作:")
        print("1. 查看所有股票概览")
        print("2. 绘制特定股票的K线图")
        print("3. 退出")
        
        choice = input("请输入选择 (1-3): ").strip()
        
        if choice == '1':
            stock_codes = visualizer.show_all_stocks()
            
        elif choice == '2':
            if visualizer.transactions is None:
                print("请先加载交易数据")
                continue
                
            stock_codes = sorted(visualizer.transactions['stock_code'].unique())
            print(f"\n可用的股票代码: {', '.join(stock_codes)}")
            
            stock_code = input("请输入要查看的股票代码: ").strip()
            
            if stock_code in stock_codes:
                save_option = input("是否保存图表? (y/n): ").strip().lower()
                save_plot = save_option == 'y'
                visualizer.plot_stock_with_trades(stock_code, save_plot)
            else:
                print("股票代码不存在")
                
        elif choice == '3':
            print("感谢使用！")
            break
            
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
import numpy as np
import time
import random
import requests
import json

class StockTradingVisualizer:
    def __init__(self):
        self.transactions = None
        self.stock_info_cache = {}  # 缓存股票基本信息
        
    def load_transactions(self, file_path):
        """加载交易数据"""
        try:
            # 尝试不同的编码方式
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
            
            for encoding in encodings:
                try:
                    # 先读取文件检查是否有标题行
                    with open(file_path, 'r', encoding=encoding) as f:
                        first_line = f.readline().strip()
                    
                    # 检查第一行是否包含非数字字符（可能是标题行）
                    has_header = not first_line.split(',')[0].isdigit()
                    
                    if file_path.endswith('tdx_transaction_new.csv'):
                        # 包含价格的文件
                        if has_header:
                            df = pd.read_csv(file_path, encoding=encoding, skiprows=1, header=None, 
                                           names=['date', 'stock_code', 'direction', 'price'])
                        else:
                            df = pd.read_csv(file_path, encoding=encoding, header=None, 
                                           names=['date', 'stock_code', 'direction', 'price'])
                    else:
                        # 不包含价格的文件
                        if has_header:
                            df = pd.read_csv(file_path, encoding=encoding, skiprows=1, header=None,
                                           names=['date', 'stock_code', 'direction'])
                        else:
                            df = pd.read_csv(file_path, encoding=encoding, header=None,
                                           names=['date', 'stock_code', 'direction'])
                        df['price'] = None
                    break
                except UnicodeDecodeError:
                    continue
            else:
                st.error("无法读取文件，请检查文件编码")
                return False
                
            # 数据处理
            # 过滤掉可能的无效行
            df = df.dropna(subset=['date', 'stock_code', 'direction'])
            
            # 尝试多种日期格式解析
            try:
                # 首先尝试标准格式
                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            except ValueError:
                try:
                    # 尝试其他可能的格式
                    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
                except ValueError:
                    try:
                        # 让pandas自动推断格式
                        df['date'] = pd.to_datetime(df['date'])
                    except ValueError as e:
                        st.error(f"日期格式解析失败: {str(e)}")
                        return False
            
            # 确保股票代码保持为字符串格式，避免前导零被截断
            df['stock_code'] = df['stock_code'].astype(str).str.zfill(6)
            df['action'] = df['direction'].map({1: '买入', 2: '卖出'})
            
            # 过滤掉无效的交易记录
            df = df[df['action'].notna()]
            
            if len(df) == 0:
                st.error("文件中没有有效的交易记录")
                return False
            
            self.transactions = df
            st.success(f"成功加载 {len(df)} 条交易记录")
            return True
            
        except Exception as e:
            st.error(f"加载文件时出错: {str(e)}")
            return False
    
    def get_stock_data_eastmoney(self, stock_code, start_date, end_date):
        """使用东方财富免费接口获取股票K线数据"""
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
            
            st.info(f"正在从东方财富获取股票 {stock_code} 的数据...")
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    if data.get('data') and data['data'].get('klines'):
                        klines = data['data']['klines']
                        
                        if not klines:
                            st.warning(f"东方财富返回空数据，股票代码 {stock_code} 可能不存在")
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
                            except (ValueError, IndexError) as e:
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
                            
                            st.success(f"✅ 东方财富接口成功获取 {len(df)} 条K线数据")
                            return df
                        else:
                            st.warning("东方财富数据解析失败，数据格式可能有问题")
                    else:
                        st.warning("东方财富接口返回数据格式异常")
                        
                except Exception as e:
                    st.warning(f"东方财富接口返回数据解析失败: {str(e)}")
            else:
                st.warning(f"东方财富接口请求失败，状态码: {response.status_code}")
            
            return None
            
        except requests.exceptions.Timeout:
            st.warning("东方财富接口请求超时")
            return None
        except requests.exceptions.ConnectionError:
            st.warning("东方财富接口连接失败")
            return None
        except Exception as e:
            st.warning(f"东方财富接口异常: {str(e)}")
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
        
        for attempt in range(max_retries):
            try:
                # 添加随机延迟以避免频率限制
                if attempt > 0:
                    delay = random.uniform(2, 5) * (attempt + 1)
                    st.info(f"正在重试获取股票数据，等待 {delay:.1f} 秒...")
                    time.sleep(delay)
                
                # 获取股票数据
                stock = yf.Ticker(symbol)
                data = stock.history(start=start_date, end=end_date)
                
                if data.empty:
                    st.warning(f"无法获取股票 {stock_code} 的数据，可能该股票不存在或已退市")
                    return None
                    
                return data
                
            except Exception as e:
                error_msg = str(e).lower()
                if "rate limit" in error_msg or "too many requests" in error_msg:
                    if attempt < max_retries - 1:
                        st.warning(f"API频率限制，正在重试... (尝试 {attempt + 1}/{max_retries})")
                        continue
                    else:
                        st.error("API频率限制，请稍后再试。建议：\n1. 等待几分钟后重试\n2. 或者尝试查看其他股票")
                        return None
                else:
                    st.error(f"获取股票数据时出错: {str(e)}")
                    return None
        
        return None
    
    def get_stock_info(self, stock_code):
        """获取股票基本信息（名称、板块等）"""
        if stock_code in self.stock_info_cache:
            return self.stock_info_cache[stock_code]
        
        try:
            # 使用东方财富接口获取股票基本信息
            stock_code = str(stock_code)
            
            if stock_code.startswith('6'):
                market_code = f"1.{stock_code}"
            elif stock_code.startswith('0') or stock_code.startswith('3'):
                market_code = f"0.{stock_code}"
            else:
                market_code = stock_code
            
            # 尝试第一个接口获取完整信息
            url1 = "http://push2.eastmoney.com/api/qt/stock/get"
            params1 = {
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'invt': '2',
                'fltt': '2',
                'fields': 'f12,f14,f58,f127,f116',  # 增加更多字段
                'secid': market_code
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'http://quote.eastmoney.com/'
            }
            
            response = requests.get(url1, params=params1, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    stock_data = data['data']
                    name = stock_data.get('f14') or stock_data.get('f58')
                    if name:
                        info = {
                            'name': name,
                            'sector': stock_data.get('f127', '未知板块'),
                            'industry': str(stock_data.get('f116', '未知行业'))
                        }
                        self.stock_info_cache[stock_code] = info
                        return info
            
            # 如果第一个接口没有获取到名称，尝试第二个接口
            url2 = "http://qt.gtimg.cn/q=s_sh000001,s_sz000001"
            if stock_code.startswith('6'):
                tencent_code = f"sh{stock_code}"
            elif stock_code.startswith('0') or stock_code.startswith('3'):
                tencent_code = f"sz{stock_code}"
            else:
                tencent_code = stock_code
            
            url2 = f"http://qt.gtimg.cn/q={tencent_code}"
            response2 = requests.get(url2, headers=headers, timeout=10)
            
            if response2.status_code == 200:
                content = response2.text.strip()
                if content and '~' in content:
                    try:
                        # 解析腾讯接口返回的数据
                        data_part = content.split('="')[1].rstrip('";')
                        fields = data_part.split('~')
                        if len(fields) >= 2:
                            name = fields[1]  # 第二个字段是股票名称
                            info = {
                                'name': name,
                                'sector': '未知板块',
                                'industry': '未知行业'
                            }
                            self.stock_info_cache[stock_code] = info
                            return info
                    except Exception:
                        pass
                        
        except Exception as e:
            pass
        
        # 如果获取失败，返回默认值
        default_info = {
            'name': f'股票{stock_code}',
            'sector': '未知板块',
            'industry': '未知行业'
        }
        self.stock_info_cache[stock_code] = default_info
        return default_info
    
    def calculate_trade_performance(self, stock_code):
        """计算股票交易表现"""
        if self.transactions is None:
            return None
        
        stock_trades = self.transactions[self.transactions['stock_code'] == stock_code].copy()
        if len(stock_trades) == 0 or stock_trades['price'].isna().all():
            return None
        
        # 按日期排序
        stock_trades = stock_trades.sort_values('date')
        
        # 计算每次买卖的盈亏
        trades_with_profit = []
        buy_stack = []  # 买入栈
        
        for _, trade in stock_trades.iterrows():
            if trade['direction'] == 1:  # 买入
                buy_stack.append(trade)
            elif trade['direction'] == 2 and buy_stack:  # 卖出且有买入记录
                buy_trade = buy_stack.pop(0)  # FIFO
                profit_pct = (trade['price'] - buy_trade['price']) / buy_trade['price'] * 100
                trades_with_profit.append({
                    'buy_date': buy_trade['date'],
                    'sell_date': trade['date'],
                    'buy_price': buy_trade['price'],
                    'sell_price': trade['price'],
                    'profit_pct': profit_pct,
                    'is_profit': profit_pct > 0
                })
        
        if not trades_with_profit:
            return None
        
        # 计算统计数据
        total_trades = len(trades_with_profit)
        profitable_trades = sum(1 for t in trades_with_profit if t['is_profit'])
        win_rate = profitable_trades / total_trades * 100 if total_trades > 0 else 0
        
        total_profit = sum(t['profit_pct'] for t in trades_with_profit if t['is_profit'])
        total_loss = abs(sum(t['profit_pct'] for t in trades_with_profit if not t['is_profit']))
        profit_loss_ratio = total_profit / total_loss if total_loss > 0 else float('inf')
        
        return {
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'win_rate': win_rate,
            'profit_loss_ratio': profit_loss_ratio,
            'trades_detail': trades_with_profit
        }
    
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
            
            st.info(f"正在从腾讯接口获取股票 {stock_code} 的数据...")
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text.strip()
                
                if content and '~' in content:
                    # 解析腾讯接口返回的数据
                    # 格式: v_sh600000="1~平安银行~000001~11.50~11.48~11.48~..."
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
                            
                            st.success(f"✅ 腾讯接口获取到实时数据")
                            return df
                    except (ValueError, IndexError) as e:
                        st.warning(f"腾讯接口数据解析失败: {str(e)}")
                else:
                    st.warning("腾讯接口返回数据格式异常")
            else:
                st.warning(f"腾讯接口请求失败，状态码: {response.status_code}")
            
            return None
            
        except Exception as e:
            st.warning(f"腾讯接口异常: {str(e)}")
            return None
    
    def get_stock_data(self, stock_code, start_date, end_date, max_retries=3):
        """获取股票K线数据 - 优先使用国内数据源"""
        # 首先尝试东方财富接口
        data = self.get_stock_data_eastmoney(stock_code, start_date, end_date)
        if data is not None and not data.empty:
            return data
        
        # 如果失败，尝试腾讯接口
        st.info("东方财富接口获取失败，尝试腾讯接口...")
        data = self.get_stock_data_tencent(stock_code, start_date, end_date)
        if data is not None and not data.empty:
            return data
        
        # 最后尝试Yahoo Finance
        st.info("腾讯接口也失败，尝试Yahoo Finance...")
        return self.get_stock_data_yahoo(stock_code, start_date, end_date, max_retries)
    
    def plot_stock_with_trades(self, stock_code):
        """绘制带交易标记的K线图"""
        if self.transactions is None:
            st.error("请先加载交易数据")
            return
        
        # 筛选该股票的交易记录
        stock_trades = self.transactions[self.transactions['stock_code'] == stock_code].copy()
        
        if stock_trades.empty:
            st.warning(f"没有找到股票 {stock_code} 的交易记录")
            return
        
        # 确定日期范围
        start_date = stock_trades['date'].min() - timedelta(days=30)
        end_date = stock_trades['date'].max() + timedelta(days=30)
        
        # 获取股票数据
        stock_data = self.get_stock_data(stock_code, start_date, end_date)
        
        if stock_data is None:
            return
        
        # 创建子图布局 - K线图和成交量图
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=(f'股票 {stock_code} K线图', '成交量'),
            row_heights=[0.8, 0.2]  # K线图占80%，成交量图占20%
        )
        
        # 添加K线 - 设置为红涨绿跌
        fig.add_trace(go.Candlestick(
            x=stock_data.index,
            open=stock_data['Open'],
            high=stock_data['High'],
            low=stock_data['Low'],
            close=stock_data['Close'],
            name=f'{stock_code} K线',
            increasing_line_color='red',  # 上涨为红色
            decreasing_line_color='green',  # 下跌为绿色
            increasing_fillcolor='red',
            decreasing_fillcolor='green'
        ), row=1, col=1)
        
        # 添加成交量柱状图
        if 'Volume' in stock_data.columns:
            # 根据涨跌设置成交量颜色
            colors = []
            for i in range(len(stock_data)):
                if stock_data['Close'].iloc[i] >= stock_data['Open'].iloc[i]:
                    colors.append('red')  # 上涨日成交量为红色
                else:
                    colors.append('green')  # 下跌日成交量为绿色
            
            fig.add_trace(go.Bar(
                x=stock_data.index,
                y=stock_data['Volume'],
                name='成交量',
                marker_color=colors,
                opacity=0.7
            ), row=2, col=1)
        
        # 添加交易标记
        buy_trades = stock_trades[stock_trades['direction'] == 1]
        sell_trades = stock_trades[stock_trades['direction'] == 2]
        
        # 买入标记
        if not buy_trades.empty:
            buy_prices = []
            for _, trade in buy_trades.iterrows():
                trade_date = trade['date']
                # 找到最接近的交易日价格
                closest_data = stock_data[stock_data.index >= trade_date]
                if not closest_data.empty:
                    price = trade['price'] if pd.notna(trade['price']) else closest_data.iloc[0]['Low']
                    buy_prices.append(price)
                else:
                    buy_prices.append(None)
            
            fig.add_trace(go.Scatter(
                x=buy_trades['date'],
                y=buy_prices,
                mode='markers',
                marker=dict(symbol='triangle-up', size=12, color='red'),
                name='买入',
                text=[f"买入 {price:.2f}" if price else "买入" for price in buy_prices],
                hovertemplate='%{text}<br>日期: %{x}<extra></extra>'
            ), row=1, col=1)
        
        # 卖出标记
        if not sell_trades.empty:
            sell_prices = []
            for _, trade in sell_trades.iterrows():
                trade_date = trade['date']
                # 找到最接近的交易日价格
                closest_data = stock_data[stock_data.index >= trade_date]
                if not closest_data.empty:
                    price = trade['price'] if pd.notna(trade['price']) else closest_data.iloc[0]['High']
                    sell_prices.append(price)
                else:
                    sell_prices.append(None)
            
            fig.add_trace(go.Scatter(
                x=sell_trades['date'],
                y=sell_prices,
                mode='markers',
                marker=dict(symbol='triangle-down', size=12, color='green'),
                name='卖出',
                text=[f"卖出 {price:.2f}" if price else "卖出" for price in sell_prices],
                hovertemplate='%{text}<br>日期: %{x}<extra></extra>'
            ), row=1, col=1)
        
        # 设置图表布局
        fig.update_layout(
            title=f'股票 {stock_code} K线图及交易记录',
            xaxis_rangeslider_visible=False,
            height=800,  # 增加高度以容纳成交量图
            width=None,  # 让图表自适应容器宽度
            margin=dict(l=50, r=50, t=80, b=50),
            showlegend=True
        )
        
        # 更新子图的轴标签
        fig.update_xaxes(title_text="日期", row=2, col=1)
        fig.update_yaxes(title_text="价格", row=1, col=1)
        fig.update_yaxes(title_text="成交量", row=2, col=1)
        
        # 使用全宽度显示图表
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
        
        # 显示交易统计
        st.subheader(f"股票 {stock_code} 交易统计")
        
        # 获取交易表现数据
        performance = self.calculate_trade_performance(stock_code)
        
        if performance:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("总交易次数", len(stock_trades))
            with col2:
                st.metric("买入次数", len(buy_trades))
            with col3:
                st.metric("卖出次数", len(sell_trades))
            with col4:
                st.metric("胜率", f"{performance['win_rate']:.1f}%")
            with col5:
                if performance['profit_loss_ratio'] == float('inf'):
                    ratio_text = "∞ (无亏损)"
                else:
                    ratio_text = f"{performance['profit_loss_ratio']:.2f}"
                st.metric("盈亏率", ratio_text)
        else:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("总交易次数", len(stock_trades))
            with col2:
                st.metric("买入次数", len(buy_trades))
            with col3:
                st.metric("卖出次数", len(sell_trades))
            
            st.info("💡 无价格数据，无法计算胜率和盈亏率")
        
        # 显示交易明细
        st.subheader("交易明细")
        
        if performance and performance['trades_detail']:
            # 显示配对的买卖交易及盈亏
            st.write("**配对交易记录（含盈亏）：**")
            
            trades_detail = []
            for trade in performance['trades_detail']:
                trades_detail.append({
                    '买入日期': trade['buy_date'].strftime('%Y-%m-%d'),
                    '买入价格': f"{trade['buy_price']:.2f}",
                    '卖出日期': trade['sell_date'].strftime('%Y-%m-%d'),
                    '卖出价格': f"{trade['sell_price']:.2f}",
                    '盈亏百分比': f"{trade['profit_pct']:+.2f}%",
                    '盈亏状态': '盈利' if trade['is_profit'] else '亏损'
                })
            
            trades_df = pd.DataFrame(trades_detail)
            st.dataframe(trades_df, use_container_width=True)
            
            st.write("**所有交易记录：**")
        
        # 显示所有交易记录
        display_trades = stock_trades[['date', 'action', 'price']].copy()
        display_trades['date'] = display_trades['date'].dt.strftime('%Y-%m-%d')
        
        # 重命名列
        display_trades = display_trades.rename(columns={
            'date': '交易日期',
            'action': '操作类型',
            'price': '交易价格'
        })
        
        # 格式化价格显示
        if not display_trades['交易价格'].isna().all():
            display_trades['交易价格'] = display_trades['交易价格'].apply(
                lambda x: f"{x:.2f}" if pd.notna(x) else "无价格数据"
            )
        
        st.dataframe(display_trades, use_container_width=True, hide_index=True)

def main():
    st.set_page_config(page_title="股票交易可视化工具", layout="wide")
    
    st.title("📈 股票交易可视化工具")
    st.markdown("---")
    
    # 初始化可视化器
    if 'visualizer' not in st.session_state:
        st.session_state.visualizer = StockTradingVisualizer()
    
    visualizer = st.session_state.visualizer
    
    # 左侧栏 - 数据导入区域（可展开收起）
    with st.sidebar:
        st.header("📁 数据导入")
        
        # 文件选择
        file_option = st.selectbox(
            "选择交易数据文件",
            ["tdx_transaction_new.csv", "tdx_transaction2.csv", "自定义文件"]
        )
        
        if file_option == "自定义文件":
            uploaded_file = st.file_uploader("上传CSV文件", type=['csv'])
            if uploaded_file is not None:
                # 保存上传的文件
                with open(f"temp_{uploaded_file.name}", "wb") as f:
                    f.write(uploaded_file.getbuffer())
                file_path = f"temp_{uploaded_file.name}"
            else:
                file_path = None
        else:
            file_path = f"c:\\Users\\X1 Yoga\\Saved Games\\AIcode\\{file_option}"
        
        if st.button("加载数据", type="primary") and file_path:
            visualizer.load_transactions(file_path)
            st.success("数据加载成功！")
        
        # 显示数据表（如果数据已加载）
        if visualizer.transactions is not None:
            st.subheader("📋 交易数据预览")
            
            # 显示数据统计信息
            total_records = len(visualizer.transactions)
            unique_stocks = visualizer.transactions['stock_code'].nunique()
            date_range = f"{visualizer.transactions['date'].min().strftime('%Y-%m-%d')} 至 {visualizer.transactions['date'].max().strftime('%Y-%m-%d')}"
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总记录数", total_records)
            with col2:
                st.metric("股票数量", unique_stocks)
            with col3:
                st.metric("日期范围", "")
                st.caption(date_range)
            
            # 显示可拖动的数据表
            display_data = visualizer.transactions[['date', 'stock_code', 'action', 'price']].copy()
            display_data['date'] = display_data['date'].dt.strftime('%Y-%m-%d')
            display_data = display_data.rename(columns={
                'date': '日期',
                'stock_code': '股票代码', 
                'action': '操作',
                'price': '价格'
            })
            
            st.dataframe(
                display_data, 
                use_container_width=True, 
                height=400,  # 设置固定高度，启用滚动
                hide_index=True
            )
    
    # 主区域 - 股票选择和图表区域
    if visualizer.transactions is not None:
        # 获取所有股票代码
        stock_codes = sorted(visualizer.transactions['stock_code'].unique())
        
        st.header("📊 股票选择")
        
        # 股票选择 - 使用更好的布局
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 为股票选择框准备格式化函数
            def format_stock_option(stock_code):
                info = visualizer.get_stock_info(stock_code)
                performance = visualizer.calculate_trade_performance(stock_code)
                
                name = info['name']
                sector = info['sector']
                
                if performance:
                    win_rate = f"{performance['win_rate']:.1f}%"
                    profit_trades = f"{performance['profitable_trades']}/{performance['total_trades']}"
                else:
                    win_rate = "无价格数据"
                    profit_trades = "--"
                
                return f"{stock_code} | {name} | {sector} | 胜率:{win_rate} ({profit_trades})"
            
            selected_stock = st.selectbox(
                "选择要查看的股票",
                stock_codes,
                format_func=format_stock_option,
                key="stock_selector"
            )
        
        with col2:
            generate_chart = st.button("生成K线图", type="secondary")
        
        # 检查股票选择是否发生变化，实现自动触发
        if 'last_selected_stock' not in st.session_state:
            st.session_state.last_selected_stock = None
        
        # 判断是否需要显示K线图（自动触发或手动点击）
        show_chart = False
        if selected_stock != st.session_state.last_selected_stock:
            # 股票选择发生变化，自动触发
            st.session_state.last_selected_stock = selected_stock
            show_chart = True
        elif generate_chart:
            # 手动点击按钮触发
            show_chart = True
        
        # 显示所有股票概览
        st.subheader("📋 交易概览")
        
        if st.checkbox("显示所有股票交易统计"):
            summary_data = []
            
            # 显示加载进度
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, stock in enumerate(stock_codes):
                status_text.text(f'正在加载股票信息... {i+1}/{len(stock_codes)}')
                progress_bar.progress((i + 1) / len(stock_codes))
                
                stock_trades = visualizer.transactions[visualizer.transactions['stock_code'] == stock]
                buy_count = len(stock_trades[stock_trades['direction'] == 1])
                sell_count = len(stock_trades[stock_trades['direction'] == 2])
                
                # 获取股票基本信息
                info = visualizer.get_stock_info(stock)
                performance = visualizer.calculate_trade_performance(stock)
                
                summary_data.append({
                    '股票代码': stock,
                    '股票名称': info['name'],
                    '所属板块': info['sector'],
                    '总交易次数': len(stock_trades),
                    '买入次数': buy_count,
                    '卖出次数': sell_count,
                    '胜率': f"{performance['win_rate']:.1f}%" if performance else "无价格数据",
                    '盈亏率': f"{performance['profit_loss_ratio']:.2f}" if performance and performance['profit_loss_ratio'] != float('inf') else "∞" if performance else "--",
                    '首次交易': stock_trades['date'].min().strftime('%Y-%m-%d'),
                    '最后交易': stock_trades['date'].max().strftime('%Y-%m-%d')
                })
            
            # 清除进度显示
            progress_bar.empty()
            status_text.empty()
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, height=400)
    else:
        st.info("👈 请在左侧选择并加载交易数据文件")
        
        # 显示示例数据格式
        st.subheader("📝 数据格式说明")
        st.markdown("""
        支持的CSV文件格式：
        
        **格式1（包含价格）：**
        ```
        20240103,000669,1,2.28
        20240103,603030,1,2.78
        ```
        
        **格式2（不包含价格）：**
        ```
        20240103,000669,1
        20240103,603030,1
        ```
        
        **字段说明：**
        - 第1列：交易日期（YYYYMMDD格式）
        - 第2列：股票代码
        - 第3列：交易方向（1=买入，2=卖出）
        - 第4列：交易价格（可选）
        """)
    
    # K线图显示区域 - 全宽度显示
    if visualizer.transactions is not None:
        # 检查是否有选中的股票需要显示K线图
        if 'last_selected_stock' in st.session_state and st.session_state.last_selected_stock:
            selected_stock = st.session_state.last_selected_stock
            st.markdown("---")
            st.header(f"📈 股票 {selected_stock} K线图")
            visualizer.plot_stock_with_trades(selected_stock)
    


if __name__ == "__main__":
    main()
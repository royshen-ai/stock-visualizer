#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同数据源的可用性
"""

import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time
import json

def test_eastmoney_api(stock_code="000001"):
    """
    测试东方财富接口
    """
    print(f"\n=== 测试东方财富接口 - 股票代码: {stock_code} ===")
    
    try:
        # 处理股票代码格式
        if stock_code.startswith('6'):
            market_code = f"1.{stock_code}"
        elif stock_code.startswith('0') or stock_code.startswith('3'):
            market_code = f"0.{stock_code}"
        else:
            market_code = stock_code
        
        print(f"市场代码: {market_code}")
        
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
        
        print(f"请求URL: {url}")
        print(f"请求参数: {params}")
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"响应数据结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                
                if data.get('data'):
                    stock_data = data['data']
                    print(f"股票数据字段: {list(stock_data.keys()) if isinstance(stock_data, dict) else type(stock_data)}")
                    
                    if stock_data.get('klines'):
                        klines = stock_data['klines']
                        print(f"K线数据条数: {len(klines)}")
                        if klines:
                            print(f"第一条K线数据: {klines[0]}")
                            print(f"最后一条K线数据: {klines[-1]}")
                            return True, f"成功获取{len(klines)}条K线数据"
                    else:
                        print("未找到klines字段")
                        print(f"完整响应: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
                else:
                    print("未找到data字段")
                    print(f"完整响应: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
            except json.JSONDecodeError as e:
                print(f"JSON解析错误: {e}")
                print(f"响应内容: {response.text[:500]}...")
        else:
            print(f"请求失败，响应内容: {response.text[:500]}...")
        
        return False, f"状态码: {response.status_code}"
        
    except Exception as e:
        print(f"东方财富接口测试失败: {str(e)}")
        return False, str(e)

def test_alternative_eastmoney_api(stock_code="000001"):
    """
    测试东方财富备用接口
    """
    print(f"\n=== 测试东方财富备用接口 - 股票代码: {stock_code} ===")
    
    try:
        # 处理股票代码格式
        if stock_code.startswith('6'):
            market_code = f"SH{stock_code}"
        elif stock_code.startswith('0') or stock_code.startswith('3'):
            market_code = f"SZ{stock_code}"
        else:
            market_code = stock_code
        
        # 备用接口
        url = f"http://api.finance.ifeng.com/akdaily/"
        params = {
            'code': market_code,
            'type': 'last'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"响应内容: {response.text[:200]}...")
            return True, "备用接口可用"
        
        return False, f"状态码: {response.status_code}"
        
    except Exception as e:
        print(f"备用接口测试失败: {str(e)}")
        return False, str(e)

def test_yahoo_finance(stock_code="000001.SZ"):
    """
    测试Yahoo Finance接口
    """
    print(f"\n=== 测试Yahoo Finance接口 - 股票代码: {stock_code} ===")
    
    try:
        stock = yf.Ticker(stock_code)
        data = stock.history(period="5d")
        
        if not data.empty:
            print(f"成功获取{len(data)}条数据")
            print(f"数据列: {list(data.columns)}")
            print(f"最新数据: {data.tail(1)}")
            return True, f"成功获取{len(data)}条数据"
        else:
            return False, "未获取到数据"
            
    except Exception as e:
        print(f"Yahoo Finance测试失败: {str(e)}")
        return False, str(e)

def test_tencent_api(stock_code="sz000001"):
    """
    测试腾讯股票接口
    """
    print(f"\n=== 测试腾讯股票接口 - 股票代码: {stock_code} ===")
    
    try:
        # 处理股票代码格式
        if stock_code.startswith('6'):
            tencent_code = f"sh{stock_code}"
        elif stock_code.startswith('0') or stock_code.startswith('3'):
            tencent_code = f"sz{stock_code}"
        else:
            tencent_code = stock_code
        
        url = f"http://qt.gtimg.cn/q={tencent_code}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"响应内容: {content[:200]}...")
            
            if content and '~' in content:
                return True, "腾讯接口可用"
        
        return False, f"状态码: {response.status_code}"
        
    except Exception as e:
        print(f"腾讯接口测试失败: {str(e)}")
        return False, str(e)

def main():
    """
    主测试函数
    """
    print("开始测试各个数据源...")
    
    test_stocks = ["000001", "600000", "300001"]
    
    results = {}
    
    for stock_code in test_stocks:
        print(f"\n{'='*60}")
        print(f"测试股票代码: {stock_code}")
        print(f"{'='*60}")
        
        # 测试东方财富
        success, msg = test_eastmoney_api(stock_code)
        results[f"eastmoney_{stock_code}"] = (success, msg)
        
        # 测试备用接口
        success, msg = test_alternative_eastmoney_api(stock_code)
        results[f"alternative_{stock_code}"] = (success, msg)
        
        # 测试腾讯接口
        success, msg = test_tencent_api(stock_code)
        results[f"tencent_{stock_code}"] = (success, msg)
        
        # 测试Yahoo Finance
        yahoo_code = f"{stock_code}.SZ" if stock_code.startswith(('0', '3')) else f"{stock_code}.SS"
        success, msg = test_yahoo_finance(yahoo_code)
        results[f"yahoo_{stock_code}"] = (success, msg)
        
        time.sleep(1)  # 避免请求过快
    
    # 输出测试结果
    print(f"\n{'='*60}")
    print("测试结果汇总:")
    print(f"{'='*60}")
    
    for test_name, (success, msg) in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{test_name:20} {status:10} {msg}")

if __name__ == "__main__":
    main()
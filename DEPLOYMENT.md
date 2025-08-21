# 股票可视化工具 - Streamlit Cloud 部署指南

本指南将帮助您将股票可视化工具部署到 Streamlit Cloud，这是部署 Streamlit 应用的最佳选择。

## 🎯 为什么选择 Streamlit Cloud？

- ✅ **免费使用** - 提供免费的托管服务
- ✅ **专为 Streamlit 设计** - 原生支持，无需额外配置
- ✅ **自动部署** - 连接 GitHub 后自动更新
- ✅ **简单易用** - 几分钟内完成部署
- ✅ **稳定可靠** - 由 Streamlit 官方维护

## 📋 部署前准备

### 1. 检查项目文件

确保您的项目包含以下必要文件：

```
股票可视化工具/
├── stock_trading_visualizer.py  # 主应用文件
├── requirements.txt             # 依赖包列表
├── README.md                   # 项目说明
├── *.csv                       # 示例数据文件（可选）
└── 其他 Python 文件
```

### 2. 验证 requirements.txt

确保 `requirements.txt` 包含所有必要的依赖：

```txt
streamlit>=1.28.0
pandas>=1.5.0
yfinance>=0.2.0
plotly>=5.15.0
numpy>=1.24.0
requests
```

## 🚀 部署步骤

### 步骤 1: 准备 GitHub 仓库

#### 1.1 创建 GitHub 账户
如果您还没有 GitHub 账户：
1. 访问 [github.com](https://github.com)
2. 点击 "Sign up" 注册账户
3. 验证邮箱并完成注册

#### 1.2 创建新仓库
1. 登录 GitHub 后，点击右上角的 "+" 按钮
2. 选择 "New repository"
3. 填写仓库信息：
   - **Repository name**: `stock-visualizer`（或您喜欢的名称）
   - **Description**: `股票交易可视化工具`
   - **Visibility**: 选择 "Public"（免费用户必须选择公开）
   - ✅ 勾选 "Add a README file"
4. 点击 "Create repository"

#### 1.3 上传项目文件

**方法一：通过 GitHub 网页界面**
1. 在新创建的仓库页面，点击 "uploading an existing file"
2. 将项目文件夹中的所有文件拖拽到上传区域
3. 添加提交信息：`Initial commit: 股票可视化工具`
4. 点击 "Commit changes"

**方法二：使用 Git 命令行**
```bash
# 在项目文件夹中打开终端
git init
git add .
git commit -m "Initial commit: 股票可视化工具"
git branch -M main
git remote add origin https://github.com/您的用户名/stock-visualizer.git
git push -u origin main
```

### 步骤 2: 部署到 Streamlit Cloud

#### 2.1 访问 Streamlit Cloud
1. 打开浏览器，访问 [share.streamlit.io](https://share.streamlit.io)
2. 点击 "Sign up" 或 "Continue with GitHub"
3. 使用您的 GitHub 账户登录

#### 2.2 创建新应用
1. 登录后，点击 "New app" 按钮
2. 填写应用配置：
   - **Repository**: 选择您刚创建的仓库（如 `您的用户名/stock-visualizer`）
   - **Branch**: 选择 `main`
   - **Main file path**: 输入 `stock_trading_visualizer.py`
   - **App URL**: 系统会自动生成，您也可以自定义

#### 2.3 高级设置（可选）
点击 "Advanced settings" 可以配置：
- **Python version**: 选择 `3.9` 或 `3.10`
- **Environment variables**: 如果需要设置环境变量

#### 2.4 部署应用
1. 检查所有设置无误后，点击 "Deploy!" 按钮
2. Streamlit Cloud 将开始构建您的应用
3. 构建过程通常需要 2-5 分钟

## ⚙️ 配置要求和注意事项

### 系统要求
- **Python 版本**: 3.7 - 3.11
- **内存限制**: 免费版本限制为 1GB RAM
- **CPU 限制**: 共享 CPU 资源
- **存储限制**: 仓库大小不超过 1GB

### 重要注意事项

1. **文件大小限制**
   - 单个文件不超过 100MB
   - 建议将大型数据文件存储在外部服务（如 Google Drive）

2. **网络访问**
   - 应用可以访问外部 API（如 Yahoo Finance）
   - 确保网络请求有适当的错误处理

3. **数据持久化**
   - Streamlit Cloud 不提供持久化存储
   - 用户上传的文件在会话结束后会被删除

4. **性能优化**
   - 使用 `@st.cache_data` 缓存数据加载
   - 避免在每次交互时重新加载大量数据

### 推荐的代码优化

在 `stock_trading_visualizer.py` 中添加缓存：

```python
import streamlit as st

@st.cache_data
def load_stock_data(symbol, start_date, end_date):
    """缓存股票数据加载"""
    # 您的数据加载代码
    pass

@st.cache_data
def process_transaction_data(df):
    """缓存交易数据处理"""
    # 您的数据处理代码
    pass
```

## 🔧 常见问题和解决方案

### 问题 1: 部署失败 - 依赖包安装错误

**错误信息**: `ERROR: Could not find a version that satisfies the requirement...`

**解决方案**:
1. 检查 `requirements.txt` 中的包名和版本号
2. 确保所有包都支持 Linux 环境
3. 移除或更新不兼容的包

**修复示例**:
```txt
# 错误的写法
streamlit==1.28.0

# 正确的写法
streamlit>=1.28.0
```

### 问题 2: 应用启动缓慢

**原因**: 数据加载或计算量大

**解决方案**:
1. 添加加载进度条
2. 使用数据缓存
3. 优化数据处理逻辑

**代码示例**:
```python
with st.spinner('正在加载股票数据...'):
    data = load_stock_data(symbol)
```

### 问题 3: 文件上传功能异常

**原因**: 文件大小超限或格式不支持

**解决方案**:
```python
uploaded_file = st.file_uploader(
    "选择CSV文件", 
    type=['csv'],
    help="文件大小不超过200MB"
)

if uploaded_file is not None:
    if uploaded_file.size > 200 * 1024 * 1024:  # 200MB
        st.error("文件过大，请选择小于200MB的文件")
        return
```

### 问题 4: 股票数据获取失败

**原因**: 网络问题或 API 限制

**解决方案**:
```python
import time
import random

def get_stock_data_with_retry(symbol, max_retries=3):
    for attempt in range(max_retries):
        try:
            data = yf.download(symbol)
            return data
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = random.uniform(1, 3)
                time.sleep(wait_time)
                continue
            else:
                st.error(f"无法获取股票数据: {e}")
                return None
```

### 问题 5: 应用访问速度慢

**原因**: 服务器地理位置或网络延迟

**解决方案**:
1. 优化代码性能
2. 减少不必要的网络请求
3. 使用数据缓存
4. 考虑升级到付费版本

## 📊 部署后管理

### 应用管理
1. **访问应用**: 部署成功后，您会获得一个公开的 URL
2. **查看日志**: 在 Streamlit Cloud 控制台查看应用日志
3. **更新应用**: 推送代码到 GitHub 仓库会自动触发重新部署
4. **暂停应用**: 在控制台可以暂停或删除应用

### 监控和维护
1. **性能监控**: 关注应用响应时间和错误率
2. **用户反馈**: 收集用户使用反馈
3. **定期更新**: 保持依赖包的更新
4. **备份代码**: 定期备份 GitHub 仓库

### 分享应用
部署成功后，您可以：
1. 分享应用 URL 给其他用户
2. 在 README.md 中添加应用链接
3. 在社交媒体或技术社区分享

## 🎉 部署成功！

恭喜！您的股票可视化工具现在已经成功部署到 Streamlit Cloud。

**下一步您可以**:
- 📱 在手机和电脑上测试应用
- 👥 邀请朋友和同事使用
- 🔧 根据用户反馈继续改进
- 📈 添加更多功能和分析工具

**需要帮助？**
- 📖 查看 [Streamlit 官方文档](https://docs.streamlit.io)
- 💬 访问 [Streamlit 社区论坛](https://discuss.streamlit.io)
- 🐛 在 GitHub 仓库提交 Issue

---

*祝您使用愉快！如果遇到任何问题，请随时查阅本指南或寻求技术支持。*

## 问题诊断

您遇到的 **404 NOT_FOUND** 错误是因为 Streamlit 应用无法在 Vercel 上直接运行。

### 为什么会出现这个问题？

1. **平台限制**：Vercel 主要设计用于静态网站和无服务器函数
2. **Streamlit 特性**：Streamlit 需要持续运行的 Python 服务器
3. **配置冲突**：原始的 vercel.json 配置试图将所有请求重定向到不存在的 index.html

## 解决方案

### 🎯 推荐方案：使用专门的 Streamlit 部署平台

#### 1. Streamlit Cloud（推荐）
- **优势**：免费、专为 Streamlit 设计、部署简单
- **步骤**：
  1. 将代码推送到 GitHub
  2. 访问 [streamlit.io/cloud](https://streamlit.io/cloud)
  3. 连接 GitHub 仓库
  4. 选择主文件：`stock_trading_visualizer.py`
  5. 自动部署

#### 2. Railway
- **优势**：支持 Python 应用、配置简单
- **步骤**：
  1. 访问 [railway.app](https://railway.app)
  2. 连接 GitHub 仓库
  3. Railway 会自动检测 Python 应用
  4. 添加启动命令：`streamlit run stock_trading_visualizer.py --server.port $PORT`

#### 3. Render
- **优势**：免费层、支持 Web 服务
- **步骤**：
  1. 访问 [render.com](https://render.com)
  2. 创建新的 Web Service
  3. 连接 GitHub 仓库
  4. 设置构建命令：`pip install -r requirements.txt`
  5. 设置启动命令：`streamlit run stock_trading_visualizer.py --server.port $PORT --server.address 0.0.0.0`

### 🔧 本地运行（开发测试）

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
streamlit run stock_trading_visualizer.py
```

### 📦 Docker 部署

如果您想使用容器化部署，可以创建 Dockerfile：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "stock_trading_visualizer.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

## 当前 Vercel 配置说明

我已经修复了 vercel.json 配置，现在访问您的 Vercel 部署会显示一个说明页面，解释为什么 Streamlit 无法在 Vercel 上运行，并提供替代解决方案。

## 总结

- ✅ **立即解决**：使用 Streamlit Cloud 部署
- ✅ **本地开发**：继续使用 `streamlit run` 命令
- ✅ **生产部署**：选择 Railway 或 Render
- ❌ **不推荐**：继续尝试在 Vercel 上部署 Streamlit

选择最适合您需求的部署方案，Streamlit Cloud 是最简单和推荐的选择。
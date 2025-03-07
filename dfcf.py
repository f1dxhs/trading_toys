import tkinter as tk
from tkinter import ttk, messagebox
import akshare as ak
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import mplfinance as mpf
import matplotlib.font_manager as fm
import platform

# 设置支持中文的字体
def set_chinese_font():
    system = platform.system()
    if system == 'Windows':
        font_path = 'C:/Windows/Fonts/simhei.ttf'  # 黑体
        font_properties = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = ['SimHei']
        return font_properties
    elif system == 'Darwin':  # macOS
        plt.rcParams['font.family'] = ['Arial Unicode MS']
        return fm.FontProperties(family='Arial Unicode MS')
    else:  # Linux和其他系统
        plt.rcParams['font.family'] = ['WenQuanYi Zen Hei', 'Noto Sans CJK JP']
        return fm.FontProperties(family=['WenQuanYi Zen Hei', 'Noto Sans CJK JP'])

# 应用中文字体设置
chinese_font = set_chinese_font()
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class StockStrategyTester:
    def __init__(self, root):
        self.root = root
        self.root.title("股票交易策略测试")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # 创建输入框架
        input_frame = ttk.LabelFrame(root, text="策略参数")
        input_frame.pack(fill="x", padx=10, pady=10)
        
        # 股票代码
        ttk.Label(input_frame, text="股票代码 (如: 000001 for 平安银行):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.stock_code = ttk.Entry(input_frame, width=15)
        self.stock_code.grid(row=0, column=1, padx=5, pady=5)
        self.stock_code.insert(0, "000001")  # 默认值
        
        # 初始资金
        ttk.Label(input_frame, text="初始资金 (元):").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.initial_capital = ttk.Entry(input_frame, width=15)
        self.initial_capital.grid(row=0, column=3, padx=5, pady=5)
        self.initial_capital.insert(0, "100000")  # 默认值
        
        # 分析天数
        ttk.Label(input_frame, text="分析天数:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.days_to_analyze = ttk.Entry(input_frame, width=15)
        self.days_to_analyze.grid(row=1, column=1, padx=5, pady=5)
        self.days_to_analyze.insert(0, "365")  # 默认值
        
        # 买入价格 X
        ttk.Label(input_frame, text="买入价格 X (低于此价格买入):").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.buy_price = ttk.Entry(input_frame, width=15)
        self.buy_price.grid(row=1, column=3, padx=5, pady=5)
        
        # 卖出价格 Y
        ttk.Label(input_frame, text="卖出价格 Y (高于此价格卖出):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.sell_price = ttk.Entry(input_frame, width=15)
        self.sell_price.grid(row=2, column=1, padx=5, pady=5)
        
        # 运行按钮
        self.run_button = ttk.Button(input_frame, text="运行策略测试", command=self.run_strategy)
        self.run_button.grid(row=2, column=3, padx=5, pady=5)
        
        # 创建结果展示区域
        self.results_frame = ttk.LabelFrame(root, text="策略结果")
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 创建图表和统计信息展示区域
        self.fig = plt.Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.results_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # 创建状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def fetch_stock_data(self, stock_code, days):
        """获取股票历史数据"""
        try:
            self.status_var.set("正在获取股票数据...")
            self.root.update()
            
            # 计算起始日期
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=int(days) + 10)).strftime('%Y%m%d')
            
            # 使用akshare获取A股历史数据
            stock_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                          start_date=start_date, end_date=end_date, adjust="qfq")
            
            # 确保获取足够的数据
            if len(stock_data) < int(days):
                stock_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                             start_date=(datetime.now() - timedelta(days=int(days) * 2)).strftime('%Y%m%d'), 
                                             end_date=end_date, adjust="qfq")
            
            # 处理数据
            stock_data['日期'] = pd.to_datetime(stock_data['日期'])
            stock_data = stock_data.set_index('日期')
            stock_data = stock_data.sort_index()
            
            # 只取最近的天数
            stock_data = stock_data.tail(int(days))
            
            # 重命名列以方便后续处理
            stock_data.rename(columns={
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume'
            }, inplace=True)
            
            return stock_data
        except Exception as e:
            messagebox.showerror("错误", f"获取股票数据失败: {str(e)}")
            return None
    
    def run_strategy(self):
        """运行交易策略"""
        try:
            # 获取输入参数
            stock_code = self.stock_code.get()
            initial_capital = float(self.initial_capital.get())
            days = self.days_to_analyze.get()
            buy_price = float(self.buy_price.get())
            sell_price = float(self.sell_price.get())
            
            # 验证输入
            if not stock_code or not days or not buy_price or not sell_price:
                messagebox.showwarning("警告", "请填写所有必要的参数")
                return
            
            if buy_price >= sell_price:
                messagebox.showwarning("警告", "买入价格必须低于卖出价格")
                return
            
            # 获取股票数据
            stock_data = self.fetch_stock_data(stock_code, days)
            if stock_data is None:
                return
            
            # 运行策略
            self.status_var.set("正在模拟交易策略...")
            self.root.update()
            
            # 初始化变量
            capital = initial_capital  # 当前资金
            shares = 0  # 持有股票数量
            buy_signals = []  # 买入信号
            sell_signals = []  # 卖出信号
            portfolio_value = []  # 组合价值（现金+股票）
            
            # 增加计算用的列
            stock_data['capital'] = 0.0
            stock_data['shares'] = 0
            stock_data['portfolio_value'] = 0.0
            stock_data['trade_type'] = ''
            
            # 模拟交易
            for idx, row in stock_data.iterrows():
                # 检查买入条件：价格低于X且有足够资金
                if row['low'] <= buy_price and capital >= row['low'] * 100:
                    # 计算可以买入的最大股数(按手为单位，1手=100股)
                    max_shares = int(capital / (row['low'] * 100)) * 100
                    
                    # 更新持仓
                    shares += max_shares
                    capital -= max_shares * row['low'] * (1 + 0.0003)  # 考虑手续费0.03%
                    
                    # 记录买入信号
                    buy_signals.append((idx, row['low']))
                    stock_data.loc[idx, 'trade_type'] = 'buy'
                
                # 检查卖出条件：价格高于Y且持有股票
                elif row['high'] >= sell_price and shares > 0:
                    # 更新持仓
                    capital += shares * row['high'] * (1 - 0.0003 - 0.001)  # 考虑手续费0.03%和印花税0.1%
                    
                    # 记录卖出信号
                    sell_signals.append((idx, row['high']))
                    stock_data.loc[idx, 'trade_type'] = 'sell'
                    shares = 0
                
                # 更新每日资产价值
                stock_data.loc[idx, 'capital'] = capital
                stock_data.loc[idx, 'shares'] = shares
                stock_data.loc[idx, 'portfolio_value'] = capital + shares * row['close']
            
            # 计算策略绩效
            initial_price = stock_data.iloc[0]['close']
            final_price = stock_data.iloc[-1]['close']
            final_value = stock_data.iloc[-1]['portfolio_value']
            
            # 计算买入持有策略的绩效（用于比较）
            buy_and_hold_shares = int(initial_capital / (initial_price * 100)) * 100
            buy_and_hold_value = buy_and_hold_shares * final_price + (initial_capital - buy_and_hold_shares * initial_price)
            
            # 计算最大回撤
            stock_data['cummax'] = stock_data['portfolio_value'].cummax()
            stock_data['drawdown'] = (stock_data['cummax'] - stock_data['portfolio_value']) / stock_data['cummax'] * 100
            max_drawdown = stock_data['drawdown'].max()
            
            # 计算年化收益率
            days_passed = (stock_data.index[-1] - stock_data.index[0]).days
            if days_passed > 0:
                annual_return = ((final_value / initial_capital) ** (365 / days_passed) - 1) * 100
            else:
                annual_return = 0
            
            # 计算夏普比率（简化版，用日收益率）
            stock_data['daily_return'] = stock_data['portfolio_value'].pct_change()
            sharpe_ratio = np.sqrt(252) * stock_data['daily_return'].mean() / stock_data['daily_return'].std() if stock_data['daily_return'].std() != 0 else 0
            
            # 胜率计算
            trade_days = stock_data[stock_data['trade_type'] != '']
            win_count = 0
            lose_count = 0
            prev_buy_price = 0
            
            for idx, row in trade_days.iterrows():
                if row['trade_type'] == 'buy':
                    prev_buy_price = row['low']
                elif row['trade_type'] == 'sell' and prev_buy_price > 0:
                    if row['high'] > prev_buy_price:
                        win_count += 1
                    else:
                        lose_count += 1
                    prev_buy_price = 0
            
            total_trades = win_count + lose_count
            win_rate = win_count / total_trades * 100 if total_trades > 0 else 0
            
            # 绘制结果
            self.plot_results(stock_code, stock_data, buy_signals, sell_signals, 
                             initial_capital, final_value, annual_return, max_drawdown,
                             sharpe_ratio, win_rate, buy_and_hold_value)
            
            self.status_var.set("策略测试完成")
            
        except Exception as e:
            messagebox.showerror("错误", f"策略测试出错: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def plot_results(self, stock_code, stock_data, buy_signals, sell_signals, 
                    initial_capital, final_value, annual_return, max_drawdown,
                    sharpe_ratio, win_rate, buy_and_hold_value):
        """绘制策略结果图表"""
        self.fig.clear()
        
        # 只创建一个主图表
        ax = self.fig.add_subplot(111)
        
        # 绘制股价
        ax.plot(stock_data.index, stock_data['close'], label='收盘价', color='black', alpha=0.7)
        
        # 绘制买入和卖出信号
        for date, price in buy_signals:
            ax.scatter(date, price, color='green', s=100, marker='^', alpha=0.7)
        for date, price in sell_signals:
            ax.scatter(date, price, color='red', s=100, marker='v', alpha=0.7)
        
        # 绘制买入和卖出价格水平线
        if self.buy_price.get():
            ax.axhline(y=float(self.buy_price.get()), color='green', linestyle='--', alpha=0.5, label=f'买入价 {self.buy_price.get()}')
        if self.sell_price.get():
            ax.axhline(y=float(self.sell_price.get()), color='red', linestyle='--', alpha=0.5, label=f'卖出价 {self.sell_price.get()}')
        
        # 计算买入持有策略相关数据（虽然我们不再绘制图表，但仍需计算收益率）
        buy_hold_shares = int(initial_capital / (stock_data.iloc[0]['close'] * 100)) * 100
        stock_data['buy_hold_value'] = (initial_capital - buy_hold_shares * stock_data.iloc[0]['close']) + buy_hold_shares * stock_data['close']
        
        # 设置标签和标题
        ax.set_title(f'股票 {stock_code} 交易策略测试结果', fontsize=14, fontproperties=chinese_font)
        ax.set_ylabel('股价 (元)', fontproperties=chinese_font)
        ax.set_xlabel('日期', fontproperties=chinese_font)
        
        # 将图例放在图表外部的右上方，避免遮挡数据
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.1), 
                 ncol=3, fancybox=True, shadow=True, prop=chinese_font)
        
        ax.grid(True)
        
        # 格式化x轴日期
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        self.fig.autofmt_xdate()
        
        # 添加策略绩效文本
        strategy_return = (final_value - initial_capital) / initial_capital * 100
        buy_hold_return = (buy_and_hold_value - initial_capital) / initial_capital * 100
        
        performance_text = (
            f"初始资金: {initial_capital:,.2f}元\n"
            f"最终资金: {final_value:,.2f}元\n"
            f"总收益率: {strategy_return:.2f}%\n"
            f"年化收益率: {annual_return:.2f}%\n"
            f"最大回撤: {max_drawdown:.2f}%\n"
            f"买入持有收益率: {buy_hold_return:.2f}%\n"
            f"超额收益: {strategy_return - buy_hold_return:.2f}%\n"
            f"夏普比率: {sharpe_ratio:.2f}\n"
            f"交易胜率: {win_rate:.2f}%"
        )
        
        # 在图表左上角添加文本框，确保不遮挡主要数据
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.02, 0.98, performance_text, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', bbox=props, fontproperties=chinese_font)
        
        # 让图表占用更多空间
        self.fig.subplots_adjust(top=0.85, bottom=0.15)
        
        # 显示图表
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = StockStrategyTester(root)
    root.mainloop()
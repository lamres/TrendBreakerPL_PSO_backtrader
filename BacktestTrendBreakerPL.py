import backtrader as bt
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from DataFeedFormat import FinamHLOC
from TrendBreakerPLStrategy import TrendBreakerPL
import pyfolio as pf
import seaborn as sns
sns.set_style("whitegrid")

class BacktestTrendBreakerPL:
    def __init__(self,
                 file_data,
                 algo_params,
                 output_settings
                 ):
        self.file_data = file_data
        self.algo_params = algo_params
        self.output_settings = output_settings

    def run_strategy(self, cash=1000, commission=0.0004, tf=bt.TimeFrame.Minutes, compression=60):
        cerebro = bt.Cerebro()
        cerebro.broker.setcommission(commission=commission)
        cerebro.broker.setcash(cash)

        data = FinamHLOC(dataname=self.file_data, timeframe=tf, compression=compression)

        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='returns')
        cerebro.adddata(data)
        cerebro.addstrategy(TrendBreakerPL,
                            pivot_window_len=self.algo_params['pivot_window_len'],
                            history_bars_as_multiple_pwl=self.algo_params['history_bars_as_multiple_pwl'],
                            fixed_tp=self.algo_params['fixed_tp'],
                            fixed_sl_as_multiple_tp=self.algo_params['fixed_sl_as_multiple_tp'],
                            order_full=self.output_settings['order_full'],
                            order_status=self.output_settings['order_status'],
                            trades=self.output_settings['trades'])

        if self.output_settings['performance']:
            print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
        strats = cerebro.run()
        first_strat = strats[0]

        if self.output_settings['performance']:
            print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

        od_returns = first_strat.analyzers.getbyname('returns').get_analysis()
        df_returns = pd.DataFrame(od_returns.items(), columns=['date', 'return'])
        df_returns = df_returns.set_index('date')

        self.stability = self.stability_of_timeseries(df_returns['return'])

        if self.output_settings['performance']:
            print('Performance:')
            print('Return: ' + str((cerebro.broker.getvalue() - cash) / cash * 100) + '%')
            print('Stability:' + str(self.stability))
            print('Top-5 Drawdowns:')
            print(pf.show_worst_drawdown_periods(df_returns['return'], top=5))

        if self.output_settings['plot']:
            # Read Close prices from csv and calculate the returns as a benchmark
            capital_algo = np.cumprod(1.0 + df_returns['return']) * cash
            benchmark_df = pd.read_csv(self.file_data)
            benchmark_returns = benchmark_df['<CLOSE>'].pct_change()
            capital_benchmark = np.cumprod(1.0 + benchmark_returns) * cash
            df_returns['benchmark_return'] = benchmark_returns

            # Plot Capital Curves
            plt.figure(figsize=(12, 7))
            plt.plot(np.array(capital_algo), color='blue')
            plt.plot(np.array(capital_benchmark), color='red')
            plt.legend(['Algorithm', 'Buy & Hold'])
            plt.title('Capital Curve')
            plt.xlabel('Time')
            plt.ylabel('Value')
            plt.show()

            # Plot Drawdown Underwater
            plt.figure(figsize=(12, 7))
            pf.plot_drawdown_underwater(df_returns['return']).set_xlabel('Time')
            plt.show()

            # Plot Top-5 Drawdowns
            plt.figure(figsize=(12, 7))
            pf.plot_drawdown_periods(df_returns['return'], top=5).set_xlabel('Time')
            plt.show()

            # Plot Simple Returns
            plt.figure(figsize=(12, 7))
            plt.plot(df_returns['return'], 'blue')
            plt.title('Returns')
            plt.xlabel('Time')
            plt.ylabel('Return')
            plt.show()

            # Plot Return Quantiles by Timeframe
            plt.figure(figsize=(12, 7))
            pf.plot_return_quantiles(df_returns['return']).set_xlabel('Timeframe')
            plt.show()

            # Plot Monthly Returns Dist
            plt.figure(figsize=(12, 7))
            pf.plot_monthly_returns_dist(df_returns['return']).set_xlabel('Returns')
            plt.show()


    # Determines R-squared of a linear fit to the cumulative log returns. Negative value means unprofitable result.
    def stability_of_timeseries(self, returns):
        if len(returns) < 2:
            return np.nan

        returns = np.asanyarray(returns)
        returns = returns[~np.isnan(returns)]

        cum_log_returns = np.log1p(returns).cumsum()
        rhat = stats.linregress(np.arange(len(cum_log_returns)),
                                cum_log_returns)[2]

        if cum_log_returns[0] < cum_log_returns[-1]:
            return rhat ** 2
        else:
            return -(rhat ** 2)
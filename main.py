from BacktestTrendBreakerPL import BacktestTrendBreakerPL
import backtrader as bt
import warnings
warnings.filterwarnings("ignore")

from pyswarm import pso

# The objective function for optimization
def obj_fun(x):
    print('')
    print('Launched the iteration with ' + str(x))

    ap = {'pivot_window_len': int(x[0]),
          'history_bars_as_multiple_pwl': int(x[1]),
          'fixed_tp': x[2],
          'fixed_sl_as_multiple_tp': x[3]
          }
    os = {'order_full': False,
          'order_status': False,
          'trades': False,
          'performance': True,
          'plot': False
          }

    # Creater object for Backtesting
    backtest = BacktestTrendBreakerPL(file_data='./SBER_140101_171231_hourly_train.csv',
                                      algo_params=ap,
                                      output_settings=os)
    # Run the strategy (hourly timeframe)
    backtest.run_strategy(cash=1000,
                          commission=0.0004,
                          tf=bt.TimeFrame.Minutes,
                          compression=60)

    # Add "minus" for minimization
    return -backtest.stability


# Bounds for parameters space
lb = [2, 10, 0.01, 0.1]
ub = [120, 100, 0.2, 1.5]

# Run the optimization
xopt, fopt = pso(obj_fun, lb, ub, swarmsize=20, maxiter=40)
print('OPTIMAL PARAMETERS:')
print(xopt, fopt)

# Store the best params
algo_params = {'pivot_window_len': int(xopt[0]),
               'history_bars_as_multiple_pwl': int(xopt[1]),
               'fixed_tp': xopt[2],
               'fixed_sl_as_multiple_tp': xopt[3],
               }

output_settings = {'order_full': False,
                   'order_status': False,
                   'trades': False,
                   'performance': True,
                   'plot': True
                   }

# Run the strategy with best params
# Using train, test and full datasets
for file in ['./data/SBER_140101_171231_hourly_train.csv',
          './data/SBER_180101_200224_hourly_test.csv',
          './data/SBER_140101_200224_hourly_full.csv']:
    print('Launched backtest for ' + file)
    backtest = BacktestTrendBreakerPL(file_data=file,
                                      algo_params=algo_params,
                                      output_settings=output_settings)
    backtest.run_strategy(cash=1000,
                          commission=0.0004,
                          tf=bt.TimeFrame.Minutes,
                          compression=60)



'''
# Manual fitted parameters
algo_params = {'pivot_window_len': 12,
               'history_bars_as_multiple_pwl': 30,
               'fixed_tp': 0.08,                    # Inf - off
               'fixed_sl_as_multiple_tp': 0.15,     # fixed_tp * fixed_sl_as_multiple_tp >= 1.0 - off
               }

# Just output parameters
output_settings = {'order_full': False,
                   'order_status': True,
                   'trades': True,
                   'performance': True,
                   'plot': True
                   }

backtest = BacktestTrendBreakerPL(file_data='./data/SBER_140101_200224_hourly_full.csv',
                                  algo_params=algo_params,
                                  output_settings=output_settings)
backtest.run_strategy(cash=1000,
                      commission=0.0004,
                      tf=bt.TimeFrame.Minutes,
                      compression=60)
'''
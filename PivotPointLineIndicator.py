import backtrader as bt
import pandas as pd
import numpy as np


class PivotPointLine(bt.Indicator):
    lines = ('pivot_up', 'pivot_down', 'pl_value', 'direction',)
    params = (
        ('pivot_window_len', 12),
        ('history_bars_as_multiple_pwl', 30)
    )

    def once(self, start, end):
        history_bars_length = self.params.pivot_window_len * self.params.history_bars_as_multiple_pwl

        # Define the references for the output lines
        pivot_up = self.lines.pivot_up.array
        pivot_down = self.lines.pivot_down.array
        pl_value = self.lines.pl_value.array
        pl_direction = self.lines.direction.array

        # Create the dataframe with candles for storaging price and other information
        candles = pd.DataFrame()
        for i in range(start, end):
            candles = candles.append({'open': self.data_open[i],
                                      'high': self.data_high[i],
                                      'low': self.data_low[i],
                                      'close': self.data_close[i],
                                      'pivot_up': False,
                                      'pivot_down': False,
                                      'pl_value': -1.0,
                                      'direction': 0.0},
                                     ignore_index=True)

        # Determine the pivot points
        candles['high_rolling_left'] = candles['high'].rolling(self.params.pivot_window_len + 1).apply(np.max, raw=True)
        candles['low_rolling_left'] = candles['low'].rolling(self.params.pivot_window_len + 1).apply(np.min, raw=True)
        candles['high_rolling_right'] = candles['high'][::-1].rolling(self.params.pivot_window_len + 1).apply(np.max,
                                                                                                              raw=True)
        candles['low_rolling_right'] = candles['low'][::-1].rolling(self.params.pivot_window_len + 1).apply(np.min,
                                                                                                            raw=True)
        candles['pivot_up'] = [True if x.low == x.low_rolling_left and x.low == x.low_rolling_right else False
                               for x in candles.itertuples()]
        candles['pivot_down'] = [True if x.high == x.high_rolling_left and x.high == x.high_rolling_right else False
                                 for x in candles.itertuples()]

        for i in range(history_bars_length, candles.shape[0]):
            tmp_df = candles[(i - history_bars_length):i]
            direction = 0.0
            direction_long = False
            direction_short = False
            pivot_line = -1.0

            # Check LONG direction based on Pivot Down points
            # Stupidly, but yet another one condition is not hurt
            if candles.shape[0] > 0:
                ind_current_pivot_down = -1
                potential_pivots_down = \
                    np.where(tmp_df['pivot_down'][:(-self.params.pivot_window_len)] == True)[0]
                if len(potential_pivots_down) > 0:
                    ind_current_pivot_down = potential_pivots_down[-1] + 1

                if ind_current_pivot_down > -1:
                    high_price_current_pivot_down = tmp_df['high'].iat[ind_current_pivot_down - 1]
                    # Get satisfied bars (price level and pivot point status)
                    prev_highs = np.where(
                        (tmp_df['high'][:(ind_current_pivot_down - 1)] > high_price_current_pivot_down) & (
                                tmp_df['pivot_down'][:(ind_current_pivot_down - 1)] == True))[0]

                    # If we've got these bars
                    if len(prev_highs) > 0:
                        # Get additional information
                        open_price_now = tmp_df['open'].iat[-1]
                        close_price_now = tmp_df['close'].iat[-1]
                        high_price_prev_good_pivot_down = tmp_df['high'].iat[prev_highs[-1]]
                        ind_prev_good_pivot_down = prev_highs[-1] + 1
                        num_bars_between_pivot_down_points = ind_current_pivot_down - ind_prev_good_pivot_down
                        num_bars_between_current_pivot_down_now = history_bars_length - ind_current_pivot_down

                        # Calculate trend line and make the decision
                        dydx_ratio = (
                                             high_price_current_pivot_down - high_price_prev_good_pivot_down) / num_bars_between_pivot_down_points
                        pivot_line = high_price_current_pivot_down + dydx_ratio * num_bars_between_current_pivot_down_now
                        if dydx_ratio < 0 and close_price_now > pivot_line > open_price_now:
                            direction_long = True
                            direction = 1.0

            # # Check SHORT direction based on Pivot Up points
            # Stupidly, but yet another one condition is not hurt
            if candles.shape[0] > 0:
                ind_current_pivot_up = -1
                potential_pivots_up = \
                    np.where(tmp_df['pivot_up'][:(-self.params.pivot_window_len)] == True)[0]
                if len(potential_pivots_up) > 0:
                    ind_current_pivot_up = potential_pivots_up[-1] + 1

                if ind_current_pivot_up > -1:
                    low_price_current_pivot_up = tmp_df['low'].iat[ind_current_pivot_up - 1]
                    # Get satisfied bars (price level and pivot point status)
                    prev_lows = np.where(
                        (tmp_df['low'][:(ind_current_pivot_up - 1)] < low_price_current_pivot_up) & (
                                tmp_df['pivot_up'][:(ind_current_pivot_up - 1)] == True))[0]

                    # If we've got these bars
                    if len(prev_lows) > 0:
                        # Get additional information
                        open_price_now = tmp_df['open'].iat[-1]
                        close_price_now = tmp_df['close'].iat[-1]
                        low_price_prev_good_pivot_up = tmp_df['low'].iat[prev_lows[-1]]
                        ind_prev_good_pivot_up = prev_lows[-1] + 1
                        num_bars_between_pivot_up_points = ind_current_pivot_up - ind_prev_good_pivot_up
                        num_bars_between_current_pivot_up_now = history_bars_length - ind_current_pivot_up

                        # Calculate trend line and make the decision
                        dydx_ratio = (
                                             low_price_current_pivot_up - low_price_prev_good_pivot_up) / num_bars_between_pivot_up_points
                        pivot_line = low_price_current_pivot_up + dydx_ratio * num_bars_between_current_pivot_up_now
                        if dydx_ratio > 0 and close_price_now < pivot_line < open_price_now:
                            direction_short = True
                            direction = -1.0

            # Set values only if we don't get 2 directions at the same time
            if not direction_long or not direction_short:
                candles['pl_value'].iat[i] = pivot_line
                candles['direction'].iat[i] = direction

        # Fill the output indicator lines (status of pivot points)
        # 'end - 1' - Kostyl for exception fixing
        for i in range(start, end - 1):
            pivot_up[i] = candles['pivot_up'][i]
            pivot_down[i] = candles['pivot_down'][i]
            pl_value[i] = candles['pl_value'][i]
            pl_direction[i] = candles['direction'][i]
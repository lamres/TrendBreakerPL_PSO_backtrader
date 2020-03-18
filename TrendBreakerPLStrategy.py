import backtrader as bt
from PivotPointLineIndicator import PivotPointLine

# Create a Strategy
class TrendBreakerPL(bt.Strategy):
    params = (
        ('pivot_window_len', 12),
        ('history_bars_as_multiple_pwl', 30),
        ('fixed_tp', 0.08),
        ('fixed_sl_as_multiple_tp', 0.15),
        ('order_full', False),
        ('order_status', False),
        ('trades', False)
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = self.datas[0].datetime.date(0)
        print('%s: %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.pivot_points = PivotPointLine(self.data,
                                           pivot_window_len=self.params.pivot_window_len,
                                           history_bars_as_multiple_pwl=self.params.history_bars_as_multiple_pwl)

        self.data_open = self.datas[0].open
        self.data_high = self.datas[0].high
        self.data_low = self.datas[0].low
        self.data_close = self.datas[0].close

    # Event on trade
    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        if self.params.trades:
            self.log('OPERATION PROFIT, GROSS {0:8.2f}, NET {1:8.2f}'.format(
                trade.pnl, trade.pnlcomm))

    # Event on order
    def notify_order(self, order):
        if self.params.order_full:
            print('ORDER INFO: \n' + str(order))

        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                if self.params.order_status:
                    self.log('BUY EXECUTED: ' + str(order.executed.price) + ', SIZE: ' + str(order.executed.size))
            if order.issell():
                if self.params.order_status:
                    self.log('SELL EXECUTED: ' + str(order.executed.price) + ', SIZE: ' + str(order.executed.size))

        if order.status in [order.Canceled]:
            if self.params.order_status:
                self.log('ORDER STATUS: Canceled')
        if order.status in [order.Margin]:
            if self.params.order_status:
                self.log('ORDER STATUS: Margin')
        if order.status in [order.Rejected]:
            if self.params.order_status:
                self.log('ORDER STATUS: Rejected')
        if order.status in [order.Partial]:
            if self.params.order_status:
                self.log('ORDER STATUS: Partial')

    def next(self):
        if self.pivot_points.direction[0] == 1.0 and self.position.size == 0.0:
            self.order_target_percent(target=1.0,
                                      exectype=bt.Order.Market)
            if self.params.order_status:
                self.log('BUY CREATE ORDER, %.2f' % self.data_close[0])
        if self.pivot_points.direction[0] == -1.0 and self.position.size == 0.0:
            self.order_target_percent(target=-1.0,
                                      exectype=bt.Order.Market)
            if self.params.order_status:
                self.log('SELL CREATE ORDER, %.2f' % self.data_close[0])

        # Check naive TP & SL
        # LONG
        if self.position.size > 0:
            sl = self.params.fixed_tp * self.params.fixed_sl_as_multiple_tp

            if self.position.price * (1.0 + self.params.fixed_tp) < self.data_high[0]:
                self.order_target_percent(target=0.0,
                                          exectype=bt.Order.Market)
                if self.params.order_status:
                    self.log('CLOSE LONG BY TP CREATE ORDER, %.2f' % self.data_close[0])
            if self.position.price * (1.0 - sl) > self.data_low[0]:
                self.order_target_percent(target=0.0,
                                          exectype=bt.Order.Market)
                if self.params.order_status:
                    self.log('CLOSE LONG BY SL CREATE ORDER, %.2f' % self.data_close[0])
        # SHORT
        if self.position.size < 0:
            sl = self.params.fixed_tp * self.params.fixed_sl_as_multiple_tp

            if self.position.price * (1.0 - self.params.fixed_tp) > self.data_low[0]:
                self.order_target_percent(target=0.0,
                                          exectype=bt.Order.Market)
                if self.params.order_status:
                    self.log('CLOSE SHORT BY TP CREATE ORDER, %.2f' % self.data_close[0])
            if self.position.price * (1.0 + sl) < self.data_high[0]:
                self.order_target_percent(target=0.0,
                                          exectype=bt.Order.Market)
                if self.params.order_status:
                    self.log('CLOSE SHORT BY CREATE ORDER, %.2f' % self.data_close[0])

        # Close if it's reverse direction
        if (self.position.size > 0 and self.pivot_points.direction[0] == -1.0) or (
                self.position.size < 0 and self.pivot_points.direction[0] == 1.0):
            self.order_target_percent(target=0.0,
                                      exectype=bt.Order.Market)
            if self.params.order_status:
                self.log('CLOSE POSITION BY REVERSE SIGNAL, %.2f' % self.data_close[0])
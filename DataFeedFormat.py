import backtrader.feeds as btfeed


class FinamHLOC(btfeed.GenericCSVData):
    params = (
        ('dtformat', ('%Y%m%d')),
        ('tmformat', ('%H%M%S')),
        ('datetime', 2),
        ('time', 3),
        ('high', 5),
        ('low', 6),
        ('open', 4),
        ('close', 7),
        ('volume', 8)
    )
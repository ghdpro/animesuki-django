"""AnimeSuki Core utilities"""

class DatePrecision:
    FULL = 1
    YEAR = 2
    MONTH = 3
    choices = (
        (FULL, 'Full'),
        (YEAR, 'Year'),
        (MONTH, 'Month'),
    )

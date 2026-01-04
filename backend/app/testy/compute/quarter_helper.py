from datetime import datetime


def datetime_to_year_quarter(dt: datetime) -> tuple[int, int]:
    month = dt.month
    quarter = (month - 1) // 3 + 1
    return dt.year, quarter


def shift_year_quarter(year: int, quarter: int, delta_q: int) -> tuple[int, int]:
    total = year * 4 + (quarter - 1) + delta_q
    new_year = total // 4
    new_quarter = (total % 4) + 1
    return new_year, new_quarter


def get_required_quarters(
    start_time: datetime,
    end_time: datetime,
) -> list[tuple[int, int]]:
    """
    Zwraca listę (year, quarter), które trzeba policzyć i zapisać do DB
    """

    start_y, start_q = datetime_to_year_quarter(start_time)

    end_y, end_q = datetime_to_year_quarter(end_time)

    quarters = []

    while True:
        quarters.append((start_y, start_q))

        if (start_y, start_q) == (end_y, end_q):
            break

        start_y, start_q = shift_year_quarter(start_y, start_q, 1)

    return quarters

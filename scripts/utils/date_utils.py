from datetime import date, datetime, timedelta
import calendar

from dateutil.relativedelta import relativedelta

from property.models import OCMaster

FREQ_CONVERT = {'Annual': '12',
                'Half yearly': '6',
                'Quarterly': '3',
                'Monthly': '1'
                }


def get_today():
    today = date.today()
    return today


def get_now():
    now = datetime.now()
    return now


def day_offset(cur_date, day_num):
    # add logic to support string only dd/mm/yyyy
    if type(cur_date).__name__ == 'str':
        cur_date = str_to_date(cur_date)

    return cur_date + timedelta(days=day_num)


def str_to_date(date):
    if type(date).__name__ == 'str':
        if '-' in date:
            return datetime.strptime(date, '%Y-%m-%d').date()
        if '/' in date:
            return datetime.strptime(date, '%d/%m/%Y').date()


def diff_month(to_date, from_date):
    # 13/11 change due to new logic of time difference
    return (to_date.year - from_date.year) * 12 + to_date.month - from_date.month


def year_offset(cur_date, year_num):
    return cur_date + relativedelta(years=year_num)


def month_offset(cur_date, month_num):
    return cur_date + relativedelta(months=month_num)


def date_to_str(input_date):
    return datetime.strftime(input_date, '%d/%m/%Y')


# used for db date transfer to string for db selection


def date_to_str_db(input_date):
    return datetime.strftime(input_date, '%Y-%m-%d')


def generate_date(input_date):
    if input_date == 1:
        return '1st'
    elif input_date == 2:
        return '2nd'
    elif input_date == 3:
        return '3rd'
    else:
        return str(input_date) + 'th'


def day_diff(small_date, large_date):
    """

    :param date1:
    :param date2:
    :return:
    """
    if type(small_date).__name__ == 'date' and type(large_date).__name__ == 'date':
        delta = small_date - large_date
        return delta.days
    else:
        raise Exception('function day_diff input para is not date!')


def get_fin_year(oc_id, input_date):
    oc = OCMaster.objects.get(pk=oc_id)
    billing_start_date = oc.billing_start_date
    if billing_start_date.day == 1 and billing_start_date.month == 1:
        return input_date.year
    elif input_date.month < billing_start_date.month:
        return input_date.year
    elif input_date.month == billing_start_date.month and input_date.day < billing_start_date.day:
        return input_date.year
    else:
        return input_date.year + 1


def get_defer_period_list(from_date, num_periods):
    """

    :param from_date: starting date
    :param num_periods: number of periods for amortizaiton
    :return: list of dates for amortization , and every date starting with day1
    """
    defer_date_list = []

    if type(num_periods).__name__ in ('int', 'float', 'decimal') and type(from_date).__name__ == 'date':

        from_date = from_date.replace(day=1)
        for i in range(int(num_periods)):
            defer_date_list.append(month_offset(from_date, i))
    else:
        raise Exception('invalid from date or num of period')

    return defer_date_list


def date_to_period(input_date):
    datee = None

    if isinstance(input_date, date):
        datee = input_date

    if isinstance(input_date, str):
        datee = datetime.strptime(str(input_date), "%Y-%m-%d")
        # datee = date

    if datee:
        if datee.month < 10:
            period = str(datee.year) + '0' + str(datee.month)
        else:
            period = str(datee.year) + str(datee.month)
        return period
    else:
        raise Exception("invalid input date")


def convert_date_format(date_str):
    return date_str [6:10] + '-' + date_str [3:5] + '-' + date_str [0:2]


def convert_datetime_format(date_str):
    # return date_str [6:10] + '-' + date_str [3:5] + '-' + date_str [0:2]+' '+date_str[12:17]
    return datetime(int(date_str [6:10]), int(date_str [3:5]), int(date_str [0:2]), int(date_str [12:14]),
                    int(date_str [15:17]))


def pick_billing_from(oc_id, from_date):
    oc = OCMaster.objects.get(pk=oc_id)
    base_date = oc.billing_start_date
    base_date = date(from_date.year - 1, base_date.month, base_date.day)
    frequency = int(FREQ_CONVERT [oc.frequency])
    # annual just replace with base_date.month and base_date.day
    if frequency == 12:
        return date(from_date.year, base_date.month, base_date.day)

    while True:
        # assumption  add back 28 days will have difference with real from date less than 10 days
        if abs(day_diff(base_date, from_date)) <= 10:
            return base_date
        else:
            base_date = month_offset(base_date, frequency)


def agm_date_to_str(amg_datetime):
    if type(amg_datetime).__name__ in ("datetime", "date"):
        return str(amg_datetime.day) + ' ' + calendar.month_name [amg_datetime.month] + ' ' + str(amg_datetime.year)
    else:
        return ''


def oc_financial_period(oc_id, fyear, return_type="str", end_date=None):
    base_date = OCMaster.objects.filter(pk=oc_id).first()
    if base_date:
        base_date = base_date.billing_start_date
        start_date = date(fyear - 1, base_date.month, base_date.day)
        if end_date is None:
            end_date = date(fyear, base_date.month, base_date.day)
            end_date = day_offset(end_date, -1)

        if return_type == "date":
            return start_date, end_date
        if return_type == "str":
            start_date = agm_date_to_str(start_date)
            end_date = agm_date_to_str(end_date)
            return start_date, end_date


def datetime_to_str(input_datetime):
    if len(str(input_datetime.minute)) == 1:
        min = "0" + (str(input_datetime.minute))
    else:
        min = str(input_datetime.minute)

    if len(str(input_datetime.hour)) == 1:
        hour = "0" + (str(input_datetime.hour))
    else:
        hour = str(input_datetime.hour)

    return hour + ":" + min

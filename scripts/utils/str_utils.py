from email.utils import parseaddr


def tuple_cell_to_list(input_list):
    """

    :param input_list: 2 dimensional list, every element is a tuple
    :return: list with convert every 1 element tuple to string
    """
    output_list = []
    for item in input_list:
        output_list.append(item [0])
    return output_list


def check_valid_email(mail_address):
    """
    check if input is a valid
    :param mail_address:
    :return: True/ False
    """
    if '@' in parseaddr(mail_address) [1] and '.' in parseaddr(mail_address) [1]:
        return True
    else:
        return False


def is_str_null(string):
    if string == '' or string is None:
        return True
    else:
        return False


def if_str_null(string, return_value_if_null=''):
    # default return zero length string
    if string is None or len(string) == 0:
        return return_value_if_null
    else:
        return string

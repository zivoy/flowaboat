from time import sleep

import arrow
import requests


class Api:
    def __init__(self, base_url, max_requests_per_minute=60, params=None):
        """
        expansion on the requests api that allows to limit requests and store base url as object

        :param params: any default parameters (a.e api key)
        :param base_url: base url that requests expand on
        :param max_requests_per_minute: maximum number of requests per minute
        """
        if params is None:
            params = dict()
        self.url = base_url
        self.params = params
        self.max_requests = max_requests_per_minute
        self.actions = list()

    def clear_queue(self):
        """
        clears queue
        """
        for i in self.actions.copy():
            if (arrow.utcnow() - i).seconds >= 60:
                self.actions.pop(0)
            else:
                break

    def get(self, url, params=None, **kwargs):
        """
        make get requests to api

        :param url: expands on base url
        :param params: expands on parameter dictionary
        :return: requests response
        """
        self.clear_queue()

        if len(self.actions) <= self.max_requests:
            url = self.url + url
            if params is not None:
                for k, j in self.params.items():
                    params[k] = j
            elif self.params != {}:
                params = self.params
            self.actions.append(arrow.utcnow())
            return requests.get(url, params, **kwargs)

        sleep(max(60.1 - (arrow.utcnow() - self.actions[0]).seconds, 0))
        return self.get(url, params, **kwargs)


class Dict(dict):
    """
    dict class that allows dot notation

    ex: dictObj.value
    """

    def __init__(self, *args, **kwargs):
        super(Dict, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    if isinstance(v, dict):
                        self[k] = Dict(v)
                    else:
                        self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                if isinstance(v, dict):
                    self[k] = Dict(v)
                else:
                    self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(Dict, self).__setitem__(key, value)
        self.__dict__.update({key: value})

    def __delattr__(self, item):
        self.__delitem__(item)

    def __delitem__(self, key):
        super(Dict, self).__delitem__(key)
        del self.__dict__[key]


def sanitize(text):
    """
    remove all spacial characters from text

    :param text: input text
    :return: clean text
    """
    meta_characters = ["\\", "^", "$", "{", "}", "[",
                       "]", "(", ")", ".", "*", "+",
                       "?", "|", "<", ">", "-", "&",
                       "/", ",", "!"]
    output_string = text
    for i in meta_characters:
        if i in text:
            output_string = output_string.replace(i, "")  # "\\" + i)

    return output_string


# todo: implement livelogs
class Log:
    """
    logging functions
    """

    @staticmethod
    def log(*args):
        """
        log

        :param args: anything that has to be logged
        """
        msg = f"{arrow.utcnow().isoformat()}: " + " ".join([str(i) for i in args])
        print(msg)

    @staticmethod
    def error(*args):
        """
        log any errors

        :param args: any error for logging
        """
        msg = f"{arrow.utcnow().isoformat()} -- ERROR -- : " + " ".join([str(i) for i in args])
        print(msg)


def dict_string_to_nums(dictionary):
    """
    turns all strings that are numbers into numbers inside a dict

    :param dictionary: dict
    :return: dict
    """
    for i, j in dictionary.items():
        if isinstance(j, str) and j.replace(".", "", 1).isnumeric():
            num = float(j)
            if num.is_integer():
                num = int(num)

            dictionary[i] = num
    return dictionary


def format_nums(number, decimals):
    """
    rounds to a number of decimals and if possible makes  a integer from float

    :param number: input number
    :param decimals: decimals to round to
    :return: integer or float
    """
    if round(float(number), decimals).is_integer():
        return int(f"{number:.0f}")

    return float(f"{number:.{decimals}f}")

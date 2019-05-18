import random
import time


def mytask(data):
    time.sleep(random.random() * 3)
    return data[::-1]

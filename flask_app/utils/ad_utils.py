import os
import random
from typing import List

from flask_app import app


def get_ad_paths(num: 2) -> List[str]:
    ad_folder = os.path.join(app.static_folder, 'advertisements')
    available_ads = [os.path.join(ad_folder, x) for x in os.listdir(ad_folder)]
    available_ads.sort(key=lambda x: random.randint(1, 100))
    chosen_ads = available_ads[:num]
    for x in range(len(chosen_ads)):
        with open(chosen_ads[x], 'r') as file:
            chosen_ads[x] = file.read()
    return chosen_ads



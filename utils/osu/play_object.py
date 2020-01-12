import arrow

from utils import DATE_FORM
from .utils import calculate_acc, parse_mods_int
from ..utils import dict_string_to_nums


class Play:
    def __init__(self, play_dict: dict):
        """
        organises the dict response from osu api into object

        :param play_dict: dict from api
        """
        dict_string_to_nums(play_dict)

        self.score = play_dict["score"]
        self.maxcombo = play_dict["maxcombo"]
        self.countmiss = play_dict["countmiss"]
        self.count50 = play_dict["count50"]
        self.count100 = play_dict["count100"]  # + play_dict["countkatu"]
        self.count300 = play_dict["count300"]  # + play_dict["countgeki"]
        self.perfect = play_dict["perfect"]
        self.enabled_mods = parse_mods_int(play_dict["enabled_mods"])
        self.user_id = play_dict["user_id"]
        self.date = arrow.get(play_dict["date"], DATE_FORM)
        self.rank = play_dict["rank"]
        self.accuracy = calculate_acc(self.count300, self.count100, self.count50, self.countmiss)

        if "beatmap_id" in play_dict:
            self.beatmap_id = play_dict["beatmap_id"]
        else:
            self.beatmap_id = 0

        if "replay_available" in play_dict:
            self.replay_available = play_dict["replay_available"]
        else:
            self.replay_available = 0

        if "score_id" in play_dict:
            self.score_id = play_dict["score_id"]
        else:
            self.score_id = ""

        if "pp" in play_dict:
            self.performance_points = play_dict["pp"]
        else:
            self.performance_points = None

    def __eq__(self, other):
        return self.date == other.date and self.user_id == other.user_id

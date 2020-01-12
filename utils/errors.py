class UserError(Exception):
    """
    class used to handel general user errors
    """


class UserNonexistent(UserError):
    """
    error for nonexistent user
    """


class MapError(Exception):
    """
    general errors related to maps
    """


class BadLink(MapError):
    """
    error in the case that the map link was invalid
    """


class BadMapFile(MapError):
    """
    error in the case that the map file was invalid
    """


class BadId(MapError):
    """
    error in the case that the map id was invalid
    """


class NoPlays(UserError):
    """
    error in the case that the user has no plays on map
    """


class BadMapObject(MapError):
    """
    error in the case that the map object is invalid
    """


class NoLeaderBoard(MapError):
    """
    error in the case that the there was no leader board found for map
    """


class NoBeatmap(MapError):
    """
    error in the case that there was no beatmap
    """


class NoScore(UserError):
    """
    error in the case that the user does not have a score on map
    """


class NoReplay(UserError):
    """
    error in the case that the user has no replay on the map
    """

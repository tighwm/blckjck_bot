class GameError(Exception):
    pass


class AnotherPlayerTurn(GameError):
    pass


class PlayerNotFound(GameError):
    pass

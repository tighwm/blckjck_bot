class UserException(Exception):
    pass


class BonusCooldownNotExpired(UserException):
    def __init__(self, message: str, cooldown):
        self.cooldown = cooldown
        super().__init__(message)


class BonusOnlyBellowFiveBalance(UserException):
    pass


class UserNotFound(UserException):
    pass

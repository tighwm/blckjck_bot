import random
from datetime import datetime
from typing import TYPE_CHECKING

from domain.entities import Card, Rank, Suit, Player, Dealer, PlayerResult
from domain.types.game import GameResult, ErrorType, ErrorMessages, SuccessType

if TYPE_CHECKING:
    from src.application.schemas import GameSchema


def deck_factory():
    deck = [Card(rank, suit) for suit in Suit for rank in Rank]

    random.shuffle(deck)
    return deck


class Game:
    def __init__(
        self,
        chat_id: int,
        players: dict[int, Player],
        dealer: Dealer = None,
        created_at: datetime = None,
        current_player_index: int = 0,
        round: int = 1,
        deck: list[Card] = None,
    ):
        self.chat_id = chat_id
        self.players = players
        self.dealer = dealer if dealer is not None else Dealer()
        self.created_at = created_at if created_at is not None else datetime.now()
        self.current_player_index = current_player_index
        self.round = round
        self.deck = deck if deck is not None else deck_factory()

        self.turn_order = tuple(self.players.keys())

        if not (self.dealer.first_card and self.dealer.secret_card):
            self.dealer.first_card, self.dealer.secret_card = (
                self.deck.pop(),
                self.deck.pop(),
            )
            self.dealer.cards.extend([self.dealer.first_card, self.dealer.secret_card])

    @classmethod
    def from_dto(cls, data: "GameSchema") -> "Game":
        return cls(
            chat_id=data.chat_id,
            players={
                user_tg_id: Player.from_dto(player_schema)
                for user_tg_id, player_schema in data.players.items()
            },
            dealer=Dealer.from_dto(data.dealer),
            deck=[Card.from_dto(card_schema) for card_schema in data.deck],
            created_at=data.created_at,
            current_player_index=data.current_player_index,
            round=data.round,
        )

    def _get_player_by_id(
        self,
        player_id: int,
    ):
        return self.players.get(player_id)

    def _check_is_player_turn(
        self,
        player: Player,
    ) -> bool:
        """Проверка на то, ход ли данного игрока"""
        try:
            cur_player_id = self.turn_order[self.current_player_index]
        except IndexError:
            return False
        return player.tg_id == cur_player_id

    def _check_all_bets(self) -> bool:
        return all(player.bid != 0 for player in self.players.values())

    def _check_all_have_results(self) -> bool:
        return all(player.result is not None for player in self.players.values())

    @staticmethod
    def _get_player_data(player: Player) -> dict:
        """Формирует словарь с данными игрока для ответа"""
        return {
            "player_name": player.username,
            "cards": player.cards_str(),
            "score": player.score,
            "player_id": player.tg_id,
            "bid": player.bid,
            "result": str(player.result),
        }

    def _create_game_result_with_player(
        self,
        success_type: SuccessType,
        player: Player = None,
        next_player: Player = None,
        success: bool = True,
    ) -> GameResult:
        """Создает объект GameResult с заданными параметрами"""
        data = {}
        if player:
            data["player"] = self._get_player_data(player)
            data["dealer_turn"] = True
        if success_type == SuccessType.HIT_ACCEPTED:
            data["dealer_turn"] = False
        if next_player:
            data["next_player"] = self._get_player_data(next_player)
            data["dealer_turn"] = False
        return GameResult(success=success, type=success_type, data=data)

    def get_current_turn_player(self):
        try:
            player = self.players.get(self.turn_order[self.current_player_index])
        except IndexError:
            return None
        return player

    def next_player(self) -> Player | None:
        self.current_player_index += 1
        player = self.get_current_turn_player()

        if player is None:
            return None

        if player.result is None:
            return player

        return self.next_player()

    def player_bid(
        self,
        player_id: int,
        bid: int,
    ) -> GameResult:
        player = self._get_player_by_id(player_id)
        if player is None:
            return GameResult(
                success=False,
                type=ErrorType.PLAYER_NOT_FOUND,
                message=ErrorMessages.get(
                    ErrorType.PLAYER_NOT_FOUND,
                    player_id=player_id,
                ),
            )

        player.bid = bid
        if self._check_all_bets():
            cur_player = self.get_current_turn_player()
            return GameResult(
                success=True,
                type=SuccessType.ALL_PLAYERS_BET,
                data={
                    "player": self._get_player_data(cur_player),
                    "dealer": self._get_dealer_data(),
                },
            )

        return GameResult(
            success=True,
            type=SuccessType.BID_ACCEPTED,
        )

    def player_hit(
        self,
        player_id: int,
    ) -> GameResult:
        player = self._get_player_by_id(player_id)
        if player is None:
            return GameResult(
                success=False,
                type=ErrorType.PLAYER_NOT_FOUND,
                message=ErrorMessages.get(
                    ErrorType.PLAYER_NOT_FOUND,
                    player_id=player_id,
                ),
            )

        if not self._check_is_player_turn(player=player):
            return GameResult(
                success=False,
                type=ErrorType.ANOTHER_PLAYER_TURN,
            )

        player.cards.append(self.deck.pop())

        # Обработка случая перебора
        if player.is_busted():
            player.result = PlayerResult.BUST
            next_player = self.next_player()
            return self._create_game_result_with_player(
                success_type=SuccessType.HIT_BUSTED,
                player=player,
                next_player=next_player if next_player else None,
            )

        # Обработка блэкджека
        if player.has_blackjack():
            player.result = PlayerResult.BLACKJACK
            next_player = self.next_player()
            return self._create_game_result_with_player(
                success_type=SuccessType.HIT_BLACKJACK,
                player=player,
                next_player=next_player if next_player else None,
            )

        # Стандартный случай принятия карты
        return self._create_game_result_with_player(
            success_type=SuccessType.HIT_ACCEPTED,
            player=player,
        )

    def player_stand(
        self,
        player_id: int,
    ) -> GameResult:
        player = self._get_player_by_id(player_id)
        if player is None:
            return GameResult(
                success=False,
                type=ErrorType.PLAYER_NOT_FOUND,
                message=ErrorMessages.get(
                    ErrorType.PLAYER_NOT_FOUND,
                    player_id=player_id,
                ),
            )

        if not self._check_is_player_turn(player=player):
            return GameResult(
                success=False,
                type=ErrorType.ANOTHER_PLAYER_TURN,
            )

        next_player = self.next_player()
        return self._create_game_result_with_player(
            success_type=SuccessType.STAND_ACCEPTED,
            player=player,
            next_player=next_player if next_player else None,
        )

    def init_second_round(self):
        self.round = 2
        self.current_player_index = 0

        data = {"dealer": self._get_dealer_data()}

        player = self.get_current_turn_player()
        if player.result is not None:
            player = self.next_player()
        player_data = None if player is None else self._get_player_data(player)
        data["player"] = player_data

        return data

    def _get_dealer_data(self):
        score = self.dealer.score
        return {
            "first_card": str(self.dealer.first_card),
            "secret_card": str(self.dealer.secret_card),
            "score": score - self.dealer.secret_card.get_value(),
            "score_with_secret": score,
        }

    def dealer_turns(self):
        data = []
        score = self.dealer.score
        while score < 17:
            self.dealer.cards.append(self.deck.pop())
            score = self.dealer.score
            data.append({"cards": self.dealer.cards_str(), "score": score})
        return data

    def result_of_game(self):
        wins = []
        lose = []
        push = []
        dealer_score = self.dealer.score
        for player in self.players.values():
            player_score = player.score
            if (
                player.result == PlayerResult.BUST
                or player.result == PlayerResult.OUT
                or dealer_score > player_score
            ):
                player_data = self._get_player_data(player)
                lose.append(player_data)
                continue
            if (
                player.result == PlayerResult.BLACKJACK and dealer_score == 21
            ) or player_score == dealer_score:
                player_data = self._get_player_data(player)
                player_data["amount"] = player.bid
                push.append(player_data)
                continue
            player_data = self._get_player_data(player)
            if player.result == PlayerResult.BLACKJACK:
                player_data["amount"] = player.bid * 1.5 + player.bid
            else:
                player_data["amount"] = player.bid + player.bid
            wins.append(player_data)

        data = {"wins": wins, "lose": lose, "push": push}
        return data

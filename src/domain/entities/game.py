import random
from datetime import datetime
from typing import TYPE_CHECKING, Any

from domain.entities import Card, Rank, Suit, Player, Dealer, PlayerResult
from domain.types.game.errors import AnotherPlayerTurn, PlayerNotFound

if TYPE_CHECKING:
    from src.application.schemas import GameSchema


def deck_factory():
    deck = [Card(rank, suit) for suit in Suit for rank in Rank]  # type: ignore

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
        current_round: int = 1,
        deck: list[Card] = None,
    ):
        self.chat_id = chat_id
        self.deck = deck if deck is not None else deck_factory()
        self.players = players
        self.dealer = dealer if dealer is not None else Dealer()
        self.created_at = created_at if created_at is not None else datetime.now()
        self.current_player_index = current_player_index
        self.current_round = current_round

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
            current_round=data.current_round,
        )

    def __repr__(self):
        return f"Game instance, chat_id:{self.chat_id}, round:{self.current_round}"

    def _get_player_by_id(
        self,
        player_id: int,
    ):
        return self.players.get(player_id)

    def _check_is_player_turn(
        self,
        player: Player,
    ) -> bool:
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
        return {
            "player_name": player.username,
            "cards": player.cards_str(),
            "score": player.score,
            "player_id": player.tg_id,
            "bid": player.bid,
            "result": player.result,
        }

    def _get_data_result(
        self,
        player: Player = None,
        next_player: Player = None,
        dealer_turn: bool = False,
        other_data: dict[str, Any] = None,
    ):
        data = {"dealer_action": self._dealer_action() if dealer_turn is True else None}
        if other_data:
            data += other_data
        if player:
            data["player"] = self._get_player_data(player)
        if next_player:
            data["next_player"] = self._get_player_data(next_player)
        return data

    def the_deal(self):
        data = []
        for player in self.players.values():
            if player.result == PlayerResult.OUT:
                continue
            player.cards.append(self.deck.pop())
            player.cards.append(self.deck.pop())
            if player.has_blackjack():
                player.result = PlayerResult.BLACKJACK
            data.append(self._get_player_data(player))

        return data

    def get_current_turn_player(self, data: bool = False):
        try:
            player = self.players.get(self.turn_order[self.current_player_index])
        except IndexError:
            return None
        if data:
            return self._get_player_data(player)
        return player

    def _next_player(self, data: bool = False) -> Player | dict | None:
        self.current_player_index += 1
        player = self.get_current_turn_player()

        if player is None:
            return None

        if player.result is None:
            if data:
                return self._get_player_data(player)
            return player

        return self._next_player()

    def _get_non_bid_players(self) -> list[Player]:
        non_bid = []
        for player in self.players.values():
            if player.bid == 0:
                non_bid.append(player)
        return non_bid

    def set_out_for_player(self, player_id: int):
        player = self._get_player_by_id(player_id)
        player.result = PlayerResult.OUT
        next_player = self._next_player()
        return self._get_data_result(
            player=player,
            next_player=next_player,
            dealer_turn=True if next_player is None else False,
        )

    def set_out_for_non_bid_players(self):
        not_bid_players = self._get_non_bid_players()
        data_players = []
        for player in not_bid_players:
            player.result = PlayerResult.OUT
            data_players.append(self._get_player_data(player))
        next_player = None
        if data_players:
            next_player = self._next_player()
        return self._get_data_result(
            next_player=next_player,
            other_data={"out_players": data_players},
        )

    def player_bid(
        self,
        player_id: int,
        bid: int,
    ):
        player = self._get_player_by_id(player_id)
        if player is None:
            raise PlayerNotFound(f"Player (id='{player_id}' not found")

        player.bid = bid
        if self._check_all_bets():
            cur_player = self.get_current_turn_player()
            return {
                "all_bets": True,
                "player": self._get_player_data(cur_player),
                "dealer": self._get_dealer_data(),
            }

        return {"all_bets": False}

    def player_hit(
        self,
        player_id: int,
    ):
        player = self._get_player_by_id(player_id)
        if player is None:
            raise PlayerNotFound(f"Player (id='{player_id}' not found")

        if not self._check_is_player_turn(player=player):
            raise AnotherPlayerTurn(f"Another player turn.")

        player.cards.append(self.deck.pop())

        # Обработка случая перебора
        if player.is_busted():
            player.result = PlayerResult.BUST
            next_player = self._next_player()
            return self._get_data_result(
                player=player,
                next_player=next_player,
                dealer_turn=True if next_player is None else False,
            )
        # Обработка блэкджека
        if player.has_blackjack():
            player.result = PlayerResult.BLACKJACK
            next_player = self._next_player()
            return self._get_data_result(
                player=player,
                next_player=next_player,
                dealer_turn=True if next_player is None else False,
            )
        # Стандартный случай принятия карты
        return self._get_data_result(player=player)

    def player_stand(
        self,
        player_id: int,
    ):
        player = self._get_player_by_id(player_id)
        if player is None:
            raise PlayerNotFound(f"Player (id='{player_id}' not found")

        if not self._check_is_player_turn(player=player):
            raise AnotherPlayerTurn(f"Another player turn.")

        next_player = self._next_player()
        return self._get_data_result(
            player=player,
            next_player=next_player,
            dealer_turn=True if next_player is None else False,
        )

    def _dealer_action(self):
        if self.current_round == 1:
            return {"data": self.init_second_round(), "action": "reveal"}
        if self.current_round == 2:
            return {"data": self.dealer_turns(), "action": "turns"}

    def init_second_round(self):
        self.current_round = 2
        self.current_player_index = 0

        data = {"dealer": self._get_dealer_data()}

        player = self.get_current_turn_player()
        if player.result is not None:
            player = self._next_player()
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
                or (dealer_score > player_score and not dealer_score > 21)
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

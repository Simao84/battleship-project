import random
import string
from enum import Enum
from colorama import Fore, Back, Style  # type: ignore
from src.py.interface import Game, Player


class ActionType(str, Enum):
    SET_SHIP = 'set_ship'
    SHOOT = 'shoot'


class BattleshipAction:

    def __init__(self, action_type: ActionType, ship_name: str | None, location: list[str]) -> None:
        self.action_type = action_type
        self.ship_name = ship_name
        self.location = location


class Ship:

    def __init__(self, name: str, length: int, location: list[str] | None) -> None:
        self.name = name
        self.length = length
        self.location = location


class PlayerState:

    def __init__(self, name: str, ships: list[Ship], shots: list[str], successful_shots: list[str]) -> None:
        self.name = name
        self.ships = ships
        self.shots = shots
        self.successful_shots = successful_shots


class GamePhase(str, Enum):
    SETUP = 'setup'
    RUNNING = 'running'
    FINISHED = 'finished'


class BattleshipGameState:

    def __init__(self, idx_player_active: int, phase: GamePhase, winner: int | None, players: list[PlayerState]) -> None:
        self.idx_player_active = idx_player_active
        self.phase = phase
        self.winner = winner
        self.players = players

    @staticmethod
    def get_player_board(ships: list[Ship], enemy_shots: list[str], board_size: int = 10) -> str:
        x_coords = list(string.ascii_uppercase)[:board_size]
        y_coords = [str(y) for y in range(1, board_size + 1)]
        outstring = "   " + "  ".join(x_coords) + " \n"
        ship_locations = [loc for ship in ships if ship.location is not None for loc in ship.location]
        for y_coord in y_coords:
            y_string = f"{y_coord:>2}"
            for x_coord in x_coords:
                coordinate = x_coord + y_coord
                if coordinate in ship_locations:
                    if coordinate in enemy_shots:
                        y_string += Fore.RED + Back.WHITE + Style.BRIGHT + " X " + Style.RESET_ALL
                    else:
                        y_string += Back.WHITE + " S " + Style.RESET_ALL
                else:
                    if coordinate in enemy_shots:
                        y_string += Fore.CYAN + " O " + Style.RESET_ALL
                    else:
                        y_string += " - "
            outstring += y_string + '\n'
        return outstring

    def __str__(self) -> str:
        outstring = ""
        for idx in [0, 1]:
            outstring += f"----------- Player {idx + 1} -----------\n"
            if self.winner == idx:
                outstring += Back.GREEN + Fore.YELLOW + Style.BRIGHT + "Winner!" + Style.RESET_ALL + "\n"
            elif self.idx_player_active == idx:
                outstring += Fore.YELLOW + "Your turn!" + Style.RESET_ALL + "\n"
            outstring += self.get_player_board(
                ships=self.players[idx].ships,
                enemy_shots=self.players[(idx + 1) % 2].shots
            )
            outstring += "--------------------------------\n"
        return outstring


class Battleship(Game):

    def __init__(self) -> None:
        """ Game initialization """
        self._state = BattleshipGameState(                                              # stores the game state inside the object so all other methods can access it
            idx_player_active=0,                                                        # Player 1 (index 0) goes first
            phase = GamePhase.SETUP,                                                    # ame starts in setup phase, no shooting yet, just placing ships
            winner = None,                                                              # nobody has won yet
            players = [                                                                 # both players start with no ships placed, no shots fired
                PlayerState(name='Player 1', ships=[], shots=[], successful_shots=[]), 
                PlayerState(name='Player 2', ships=[], shots=[], successful_shots=[]),
            ]
        )

    def get_state(self) -> BattleshipGameState:                                         # reads the game state
        """ Get the complete, unmasked game state """
        return self._state 

    def set_state(self, state: BattleshipGameState) -> None:                            # overwrites the game state
        """ Set the complete, unmasked game state """
        self._state = state 

    def print_state(self) -> None:                                                      # display the board in the terminal
        """ Print the current game state """
        print(self._state)

    def get_list_action(self) -> list[BattleshipAction]:
        """ Get a list of possible actions for the active player """
        actions = []
        player = self._state.players[self._state.idx_player_active]

        if self._state.phase == GamePhase.SETUP:
            ships_to_place = [
                Ship('Carrier', 5, None),
                Ship('Battleship', 4, None),
                Ship('Cruiser', 3, None),
                Ship('Submarine', 3, None),
                Ship('Destroyer', 2, None),
            ]
            already_placed = [ship.name for ship in player.ships]
            for ship in ships_to_place:
                if ship.name not in already_placed:
                    next_ship = ship
                    break

            x_coords = list(string.ascii_uppercase)[:10]
            y_coords = [str(y) for y in range(1, 11)]
            for x in x_coords:
                for y in y_coords:
                    for orientation in ['H', 'V']:
                        location = []
                        valid = True
                        for i in range(next_ship.length):
                            if orientation == 'H':
                                if x_coords.index(x) + i >= 10:
                                    valid = False
                                    break
                                location.append(x_coords[x_coords.index(x) + i] + y)
                            else:
                                if int(y) + i > 10:
                                    valid = False
                                    break
                                location.append(x + str(int(y) + i))
                        if valid:
                            actions.append(BattleshipAction(
                                action_type=ActionType.SET_SHIP,
                                ship_name=next_ship.name,
                                location=location
                            ))

        elif self._state.phase == GamePhase.RUNNING:
            opponent = self._state.players[1 - self._state.idx_player_active]
            x_coords = list(string.ascii_uppercase)[:10]
            y_coords = [str(y) for y in range(1, 11)]
            for x in x_coords:
                for y in y_coords:
                    coord = x + y
                    if coord not in player.shots:
                        actions.append(BattleshipAction(
                            action_type=ActionType.SHOOT,
                            ship_name=None,
                            location=[coord]
                        ))

        return actions    
    
    def apply_action(self, action: BattleshipAction) -> None:
        """ Apply the given action to the game """
        player = self._state.players[self._state.idx_player_active]

        if action.action_type == ActionType.SET_SHIP:
            occupied = [loc for p in self._state.players for ship in p.ships if ship.location for loc in ship.location]
            if any(loc in occupied for loc in action.location):
                return
            new_ship = Ship(
                name=action.ship_name,
                length=len(action.location),
                location=action.location
            )
            player.ships.append(new_ship)

            ships_needed = ['Carrier', 'Battleship', 'Cruiser', 'Submarine', 'Destroyer']
            placed_names = [ship.name for ship in player.ships]
            all_placed = all(name in placed_names for name in ships_needed)

            if all_placed:
                if self._state.idx_player_active == 0:
                    self._state.idx_player_active = 1
                else:
                    self._state.phase = GamePhase.RUNNING
                    self._state.idx_player_active = 0

        elif action.action_type == ActionType.SHOOT:
            coord = action.location[0]
            player.shots.append(coord)
            opponent = self._state.players[1 - self._state.idx_player_active]

            hit = False
            for ship in opponent.ships:
                if coord in ship.location:
                    player.successful_shots.append(coord)
                    hit = True
                    all_hit = all(loc in player.successful_shots for loc in ship.location)
                    if all_hit:
                        if all(
                            all(loc in player.successful_shots for loc in s.location)
                            for s in opponent.ships
                        ):
                            self._state.phase = GamePhase.FINISHED
                            self._state.winner = self._state.idx_player_active
                    break

            if not hit:
                self._state.idx_player_active = 1 - self._state.idx_player_active 

    def get_player_view(self, idx_player: int) -> BattleshipGameState:
        """ Get the masked state for the active player """
        players_view = []
        for idx, player in enumerate(self._state.players):
            if idx == idx_player:
                players_view.append(player)
            else:
                hidden_ships = [
                    Ship(name=ship.name, length=ship.length, location=None)
                    for ship in player.ships
                ]
                players_view.append(PlayerState(
                    name=player.name,
                    ships=hidden_ships,
                    shots=player.shots,
                    successful_shots=player.successful_shots
                ))
        return BattleshipGameState(
            idx_player_active=self._state.idx_player_active,
            phase=self._state.phase,
            winner=self._state.winner,
            players=players_view
        )


class RandomPlayer(Player):

    def select_action(self, state: BattleshipGameState, actions: list[BattleshipAction]) -> BattleshipAction:
        """ Given masked game state and possible actions, select the next action """
        if len(actions) == 0:
            raise ValueError('There are no actions to choose from')
        return random.choice(actions)


if __name__ == "__main__":

    game = Battleship()
    player = RandomPlayer()
    game_state = game.get_state()
    while game_state.phase != GamePhase.FINISHED:
        possible_actions = game.get_list_action()
        next_action = player.select_action(game_state, possible_actions)
        game.apply_action(next_action)
        game.print_state()
        game_state = game.get_state()
        print("\n\n")
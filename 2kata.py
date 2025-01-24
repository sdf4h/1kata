from heapq import heappop, heappush
from functools import cache
from typing import NamedTuple, TypeAlias

InitField: TypeAlias = list[list[str]]
Actions: TypeAlias = list[str]

WALL = '#'
COIN = 'C'
MERCHANT = 'M'
DOOR1 = '|'
DOOR2 = '-'
HEALTH = 'H'
KEY = 'K'
SHIELD = 'S'
DUAL_SWORDS = 'X'
ENEMY = 'E'
DEMON_LORD = 'D'
EMPTY = ' '

ATTACK = 'A'
MOVE_FORWARD = 'F'
USE_COIN = COIN
USE_KEY = KEY


class Point(NamedTuple):
    x: int
    y: int


class Move(NamedTuple):
    point: Point
    direction: str


class ResultAction(NamedTuple):
    actions: Actions
    current_hp: int
    received_damage_next_step: int
    last_action_point: Point


class Enemy:
    DEFAULT_ATTACK = 2
    DEFAULT_HP = 1

    def __init__(self, enemy_type: str) -> None:
        self.enemy_type = enemy_type
        self.attack = self.DEFAULT_ATTACK
        self.hp = self.DEFAULT_HP
        if enemy_type == DEMON_LORD:
            self.attack += 1
            self.hp *= 10

    def __str__(self) -> str:
        enemy = 'Enemy' if self.enemy_type == ENEMY else 'DemonLord'
        return f'{enemy}(attack={self.attack!r}, hp={self.hp!r})'


class Player:
    START_LEVEL = 1
    START_HP = 3
    START_ATTACK = 1
    START_DEFENSE = 1

    def __init__(self):
        self.level = self.START_LEVEL
        self.hp = self.START_HP
        self.attack = self.START_ATTACK
        self.defense = self.START_DEFENSE
        self.enemies_killed = 0
        self.bag = []

    def __str__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'level={self.level}, '
            f'health={self.hp}, '
            f'defense={self.defense}, '
            f'enemies_killed={self.enemies_killed}, '
            f'bag={sorted(self.bag)}'
            f')'
        )

    def register_defeated_enemy(self) -> None:
        self.enemies_killed += 1
        if not self.enemies_killed % 3:
            self.level += 1
            self.attack += 1

    def set_new_hp_value(self, value: int) -> None:
        self.hp = value

    def add_item_in_bag(self, item: str) -> None:
        valid_items = {COIN, KEY, HEALTH}
        if item not in valid_items:
            raise ValueError(
                f'{item=} cannot be added to the backpack; it is possible '
                f'to add one of these items: {", ".join(valid_items)}'
            )
        self.bag.append(item)

    def use_item_from_bag(self, item: str) -> None:
        try:
            self.bag.remove(item)
        except ValueError:
            raise ValueError(f'{item=!r} not in the bag')

    def equip_shield(self) -> None:
        self.defense += 1

    def equip_dual_swords(self) -> None:
        self.attack += 1

    def get_number_of_items_in_bag(self, item: str) -> int:
        return self.bag.count(item)


class Board:
    MOVES = {'>': (0, 1), '<': (0, -1), '^': (-1, 0), 'v': (1, 0)}

    def __init__(self, field: InitField) -> None:
        self.height, self.width = len(field), len(field[0])
        self.grid = field
        self.valid_points = set()

        for x, line in enumerate(field):
            for y, value in enumerate(line):
                if value == WALL:
                    continue

                point = Point(x, y)
                self.valid_points.add(point)

                if value in self.MOVES:
                    self.player_point = point
                    self.player_direction = value

        if not hasattr(self, 'player_point'):
            raise ValueError("there is no player's mark on the original map")

    def __getitem__(self, point: Point) -> str:
        return self.grid[point.x][point.y]

    def __setitem__(self, point: Point, value: str):
        self.grid[point.x][point.y] = value

    def __str__(self) -> str:
        return '\n'.join(''.join(line) for line in self.grid)

    def is_valid_point(self, point: Point) -> bool:
        return point in self.valid_points

    @cache
    def find_neighboring_points(self, point: Point) -> dict[str, Point]:
        n_points = {}
        for direction, (dx, dy) in self.MOVES.items():
            n_point = Point(x=point.x + dx, y=point.y + dy)
            if self.is_valid_point(n_point):
                n_points[direction] = n_point
        return n_points


class RPGSimulator:
    COINS_NEEDED = 3
    KEYS_NEEDED = 1

    def __init__(self, player: Player, board: Board) -> None:
        self.player = player
        self.board = board
        self.is_game_ove = False
        self.actions_to_win: Actions = []

    def destroy_demon_lord(self) -> Actions:
        while not self.is_game_ove:
            actions, hp, _, last_point = self.find_optimal_actions()
            self.actions_to_win.extend(actions)
            self.player.set_new_hp_value(hp)
            self.update(actions=actions, last_point=last_point)
        return self.actions_to_win

    def update(self, actions: Actions, last_point: Point) -> None:
        last_action = self.board[last_point]
        if last_action == DEMON_LORD:
            self.is_game_ove = True
        elif last_action == ENEMY:
            self.player.register_defeated_enemy()
        elif last_action == SHIELD:
            self.player.equip_shield()
        elif last_action == DUAL_SWORDS:
            self.player.equip_dual_swords()
        elif last_action in {KEY, HEALTH, COIN}:
            self.player.add_item_in_bag(last_action)
        elif last_action == MERCHANT:
            for _ in range(self.COINS_NEEDED):
                self.player.use_item_from_bag(COIN)
        elif last_action in {DOOR1, DOOR2}:
            self.player.use_item_from_bag(KEY)

        player_point = self.board.player_point
        player_direction = self.board.player_direction
        self.board[player_point] = player_direction

        for action in actions:
            if action in self.board.MOVES:
                self.board[player_point] = action
                player_direction = action
            elif action == MOVE_FORWARD:
                n_points = self.board.find_neighboring_points(player_point)
                self.board[player_point] = EMPTY
                player_point = n_points[player_direction]
                self.board[player_point] = player_direction
            elif action in {ATTACK, USE_KEY, USE_COIN}:
                n_points = self.board.find_neighboring_points(player_point)
                point = n_points[player_direction]
                self.board[point] = EMPTY

        self.board.player_point = player_point
        self.board.player_direction = player_direction

    def find_optimal_actions(self) -> ResultAction:
        start_point = self.board.player_point
        start_dir = self.board.player_direction
        start_move = Move(point=start_point, direction=start_dir)
        cur_hp = self.player.hp
        actions = {start_move: []}
        hp_table = {start_move: cur_hp}
        self.board[start_point] = EMPTY

        queue = [(-cur_hp, 0, start_move)]
        result = []
        while queue:
            hp, steps, move = heappop(queue)
            neighbors = self.board.find_neighboring_points(move.point)

            if self.board[move.point] != EMPTY:
                objects = [
                    self.board[p] for d, p in neighbors.items()
                    if d != move.direction
                ]
                received_damage = self.calculate_received_damage(objects)
                result_hp = hp_table[move]

                res = ResultAction(
                    actions=actions[move],
                    current_hp=result_hp,
                    received_damage_next_step=received_damage,
                    last_action_point=move.point,
                )
                if not received_damage and result_hp == self.player.START_HP:
                    return res
                result.append(res)
                continue

            objects_around = [self.board[p] for p in neighbors.values()]
            next_moves = []

            for d, point in neighbors.items():
                p = point if d == move.direction else move.point
                next_moves.append(Move(point=p, direction=d))

            for i, next_move in enumerate(next_moves):
                objs = (
                        [objects_around[i]]
                        + objects_around[:i]
                        + objects_around[i + 1:]
                )
                r_actions, r_hp = self.parse_move(
                    cur_move=next_move,
                    prev_move=move,
                    hp=hp * -1,
                    objects=objs,
                )
                if not r_actions:
                    continue

                if next_move not in hp_table or hp_table[next_move] < r_hp:
                    actions[next_move] = actions[move] + r_actions
                    hp_table[next_move] = r_hp
                    heappush(queue, (-r_hp, steps + 1, next_move))

        return min(
            result,
            key=lambda r: (
                -r.current_hp,
                r.received_damage_next_step,
                len(r.actions),
            ),
        )

    def parse_move(
            self,
            cur_move: Move,
            prev_move: Move,
            hp: int,
            objects: list[str]) -> tuple[Actions, int]:

        cell_value, *objects_around = objects
        actions = []

        if prev_move.direction != cur_move.direction:
            actions.append(cur_move.direction)
            hp -= self.calculate_received_damage(objects)

        elif cell_value in {COIN, SHIELD, DUAL_SWORDS, HEALTH, KEY, EMPTY}:
            actions.append(MOVE_FORWARD)
            hp -= self.calculate_received_damage(objects_around)

        elif cell_value == MERCHANT:
            cur_coins = self.player.get_number_of_items_in_bag(COIN)
            if cur_coins >= self.COINS_NEEDED:
                actions.extend([USE_COIN] * self.COINS_NEEDED)

        elif cell_value in {DOOR1, DOOR2}:
            cur_keys = self.player.get_number_of_items_in_bag(KEY)
            if cur_keys >= self.KEYS_NEEDED:
                actions.append(USE_KEY)

        elif cell_value == ENEMY:
            actions.append(ATTACK)
            hp -= self.calculate_received_damage(objects_around)

        else:
            boss_hp = Enemy(DEMON_LORD).hp
            first_aid_kit = self.player.get_number_of_items_in_bag(HEALTH)

            while True:
                if hp == 1 and first_aid_kit:
                    actions.append(HEALTH)
                    first_aid_kit -= 1
                    hp = self.player.START_HP
                else:
                    boss_hp -= self.player.attack
                    actions.append(ATTACK)
                if boss_hp <= 0:
                    break
                hp -= self.calculate_received_damage(objects)

        return ([], 0) if not actions or hp <= 0 else (actions, hp)

    def calculate_received_damage(self, objects: list[str]) -> int:
        received_damage = 0
        player_defense = self.player.defense
        enemies = [
            Enemy(obj) for obj in objects if obj in {DEMON_LORD, ENEMY}
        ]
        for enemy in enemies:
            received_damage += max(0, (enemy.attack - player_defense))
        return received_damage


def rpg(initial_field: InitField) -> list[str]:
    player = Player()
    board = Board(field=initial_field)
    simulator = RPGSimulator(player=player, board=board)
    return simulator.destroy_demon_lord()
    

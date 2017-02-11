from enum import Enum

import time

__author__ = 'RezaS'

direction_x = [-1, 0, 1, 0]
direction_y = [0, 1, 0, -1]


class Move(Enum):
    turn_right = 0
    step_forward = 1
    turn_left = 2


class BeetleType(Enum):
    LOW = 0
    HIGH = 1


class Cell:
    def __init__(self, x, y):
        self.row = x
        self.col = y


class Entity:
    def __init__(self, game_id, row, col):
        self.game_id = game_id
        self.row = row
        self.col = col

    def get_position(self):
        return Cell(self.row, self.col)


class Food(Entity):
    def __init__(self, datum):
        Entity.__init__(self, datum[0], datum[1], datum[2])


class Trash(Entity):
    def __init__(self, datum):
        Entity.__init__(self, datum[0], datum[1], datum[2])


class Slipper(Entity):
    def __init__(self, datum, total_valid_time):
        Entity.__init__(self, datum[0], datum[1], datum[2])
        self.remaining_time = total_valid_time

    def get_remaining_turns(self):
        return self.remaining_time


class Beetle(Entity):
    def __init__(self, datum):
        Entity.__init__(self, datum[0], datum[1], datum[2])
        self.dir = datum[3]
        self.beetle_type = datum[4]
        self.wing = datum[5]
        self.sick = datum[6]
        self.team = datum[7]

    def get_beetle_type(self):
        if self.beetle_type == 0:
            return BeetleType.LOW
        else:
            return BeetleType.HIGH

    def is_sick(self):
        return self.sick

    def has_wing(self):
        return self.wing

    def _move(self, param):
        if param == Move.turn_left:
            self.dir -= 1
            if self.dir < 0:
                self.dir += 4
        elif param == Move.step_forward:
            self.row += direction_x[self.dir]
            self.col += direction_y[self.dir]
        else:
            self.dir += 1
            if self.dir >= 4:
                self.dir -= 4


class Teleport(Entity):
    def __init__(self, datum):
        Entity.__init__(self, datum[0], datum[1], datum[2])
        self.destination_id = datum[3]


class Map:
    def __init__(self, msg, team, constants):
        self.team = team
        self.constants = constants
        self.row_number = 0
        self.col_number = 0
        self.beetles = dict()
        self.foods = dict()
        self.trashes = dict()
        self.slippers = dict()
        self.teleports = []
        self.game_map = [[]]
        self._handle_init_message(msg)

    def _handle_init_message(self, init_datum):
        self.row_number = int(init_datum[1][0])
        self.col_number = int(init_datum[1][1])

        for beetle in init_datum[2]:
            beetle_object = Beetle(beetle)
            self.beetles[beetle_object.game_id] = beetle_object

        for food in init_datum[3]:
            food_object = Food(food)
            self.foods[food_object.game_id] = food_object

        for trash in init_datum[4]:
            trash_object = Trash(trash)
            self.trashes[trash_object.game_id] = trash_object

        for slipper in init_datum[5]:
            slipper_object = Slipper(slipper, self.constants.get_slipper_valid_time())
            self.slippers[slipper_object.game_id] = slipper_object

        for teleport in init_datum[6]:
            self.teleports.append(Teleport(teleport))

    def _handle_diff(self, diff):
        diff_type = diff[ServerConstants.KEY_TYPE]
        diff_args_list = diff[ServerConstants.KEY_ARGS]
        if diff_type == ServerConstants.CHANGE_TYPE_ADD:
            for diff_args in diff_args_list:
                self._handle_add_diff(diff_args)
        elif diff_type == ServerConstants.CHANGE_TYPE_DEL:
            for diff_args in diff_args_list:
                self._handle_delete_diff(diff_args)
        elif diff_type == ServerConstants.CHANGE_TYPE_MOV:
            for diff_args in diff_args_list:
                item_game_id = diff_args[0]
                if item_game_id in self.beetles:
                    self.beetles[item_game_id]._move(diff_args[1])
        else:
            for diff_args in diff_args_list:
                item_game_id = diff_args[0]
                if item_game_id in self.beetles:
                    self.beetles[item_game_id].row = diff_args[1]
                    self.beetles[item_game_id].col = diff_args[2]
                    self.beetles[item_game_id].type = diff_args[3]
                    self.beetles[item_game_id].sick = diff_args[4]

    def _handle_delete_diff(self, diff_args):
        item_game_id = diff_args[0]
        if item_game_id in self.beetles:
            self.beetles.pop(item_game_id, None)
        if item_game_id in self.foods:
            self.foods.pop(item_game_id, None)
        if item_game_id in self.trashes:
            self.trashes.pop(item_game_id, None)
        if item_game_id in self.slippers:
            self.slippers.pop(item_game_id, None)

    def _handle_add_diff(self, diff_args):
        entity_type = diff_args[1]
        item_game_id = diff_args[0]
        if entity_type == 0:
            self.beetles[item_game_id] = Beetle(
                [diff_args[0], diff_args[2], diff_args[3], diff_args[4], diff_args[5], diff_args[6], 0, diff_args[7]])
        elif entity_type == 1:
            self.foods[item_game_id] = Food([diff_args[0], diff_args[2], diff_args[3]])
        elif entity_type == 2:
            self.trashes[item_game_id] = Trash([diff_args[0], diff_args[2], diff_args[3]])
        else:
            self.slippers[item_game_id] = Slipper([diff_args[0], diff_args[2], diff_args[3]])

    def _rebuild_game_map(self):
        self.game_map = [[0 for x in range(self.col_number)] for y in range(self.row_number)]
        for beetle in self.get_beetles_list():
            self.game_map[beetle.row][beetle.col] = beetle
        for slipper in self.get_slippers_list():
            self.game_map[slipper.row][slipper.col] = slipper
        for trash in self.get_trashes_list():
            self.game_map[trash.row][trash.col] = trash
        for food in self.get_foods_list():
            self.game_map[food.row][food.col] = food
        for teleport in self.get_teleport_list():
            self.game_map[teleport.row][teleport.col] = teleport

    # Client APIs

    def get_height(self):
        return self.row_number

    def get_width(self):
        return self.col_number

    def get_beetles_list(self):
        return self.beetles.values()

    def get_slippers_list(self):
        return self.slippers.values()

    def get_trashes_list(self):
        return self.trashes.values()

    def get_foods_list(self):
        return self.foods.values()

    def get_teleport_list(self):
        return self.teleports

    def get_game_2d_table(self):
        return self.game_map

    def get_my_beetles(self):
        return [beetle for beetle in self.beetles if beetle.team == self.team]

    def get_opponent_beetles(self):
        return [beetle for beetle in self.beetles if beetle.team != self.team]


class Constants:
    def __init__(self, msg):
        self._handle_init_message(msg)

    def _handle_init_message(self, msg):
        self.constants = msg
        self.turn_timeout = int(self.constants[0])
        self.food_prob = float(self.constants[1])
        self.trash_prob = float(self.constants[2])
        self.slipper_prob = float(self.constants[3])
        self.slipper_valid_time = int(self.constants[4])
        self.type_cost = int(self.constants[5])
        self.sick_cost = int(self.constants[6])
        self.update_cost = int(self.constants[7])
        self.det_move_cost = int(self.constants[8])
        self.kill_wing_score = int(self.constants[9])
        self.kill_both_wing_score = int(self.constants[10])
        self.kill_beetle_score = int(self.constants[11])
        self.wing_collision_score = int(self.constants[12])
        self.fish_food_score = int(self.constants[13])
        self.wing_food_score = int(self.constants[14])
        self.sick_life_time = int(self.constants[15])
        self.power_ratio = float(self.constants[16])
        self.end_ratio = float(self.constants[17])
        self.disobey_num = int(self.constants[18])
        self.food_valid_time = int(self.constants[19])
        self.trash_valid_time = int(self.constants[20])
#        self.total_turn_number = int(self.constants[21])

    def get_turn_timeout(self):
        return self.turn_timeout

    def get_food_prob(self):
        return self.food_prob

    def get_trash_prob(self):
        return self.trash_prob

    def get_slipper_prob(self):
        return self.slipper_prob

    def get_slipper_valid_time(self):
        return self.slipper_valid_time

    def get_type_cost(self):
        return self.type_cost

    def get_sick_cost(self):
        return self.sick_cost

    def get_update_cost(self):
        return self.update_cost

    def get_det_move_cost(self):
        return self.det_move_cost

    def get_kill_wing_score(self):
        return self.turn_timeout

    def get_kill_both_wing_score(self):
        return self.kill_both_wing_score

    def get_kill_beetle_score(self):
        return self.kill_beetle_score

    def get_wing_collision_score(self):
        return self.wing_collision_score

    def get_fish_food_score(self):
        return self.fish_food_score

    def get_wing_food_score(self):
        return self.wing_food_score

    def get_sick_life_time(self):
        return self.sick_life_time

    def get_power_ratio(self):
        return self.power_ratio

    def get_end_ratio(self):
        return self.end_ratio

    def get_disobey_num(self):
        return self.disobey_num

    def get_food_valid_time(self):
        return self.food_valid_time

    def get_trash_valid_time(self):
        return self.trash_valid_time

    def get_total_turns(self):
        return self.total_turn_number


class World:
    def __init__(self, queue):
        self.turn_start_time = None
        self.my_game_id = 0
        self.game_map = None
        self.turn_number = 0
        self.scores = []
        self.constants = None
        self.queue = queue

    def _handle_init_message(self, msg):
        init_datum = msg[ServerConstants.KEY_ARGS]
        self.my_game_id = int(init_datum[0])
        self.constants = Constants(init_datum[7])
        self.game_map = Map(init_datum, self.my_game_id, self.constants)

    def _handle_turn_message(self, msg):
        for slipper in self.game_map.get_slippers_list():
            slipper.remaining_time -= 1

        self.turn_start_time = int(round(time.time() * 1000))

        current_datum = msg[ServerConstants.KEY_ARGS]
        self.turn_number = int(current_datum[0])
        self.scores = current_datum[1]

        diffs = msg[ServerConstants.KEY_ARGS][2]
        for diff in diffs:
            self.game_map._handle_diff(diff)
        self.game_map._rebuild_game_map()

    # Client APIs

    def get_turn_time_passed(self):
        return int(round(time.time() * 1000)) - self.turn_start_time

    def get_turn_remaining_time(self):
        return self.constants.turn_timeout - self.get_turn_time_passed()

    def get_current_turn(self):
        return int(self.turn_number)

    def get_team_id(self):
        return int(self.my_game_id)

    def get_my_score(self):
        return int(self.scores[0])

    def get_opponent_score(self):
        return int(self.scores[1])

    def change_strategy(self, beetle_type, front_right, front, front_left, move_strategy):
        self.queue.put(Event('s', [[beetle_type, front_right, front, front_left, move_strategy.value]]))

    def deterministic_move(self, beetle, move):
        self.queue.put(Event('m', [[beetle.game_id, move.value]]))

    def change_type(self, beetle, new_type):
        self.queue.put(Event('c', [[beetle.game_id, new_type]]))

    def get_map(self):
        return self.game_map

    def get_constants(self):
        return self.constants


class Event:
    EVENT = "event"

    def __init__(self, type, args):
        self.type = type
        self.args = args

    def add_arg(self, arg):
        self.args.append(arg)

        # def to_message(self):
        #    return {
        #        'name': Event.EVENT,
        #        'args': [{'type': self.type, 'args': self.args}]
        #    }


class ServerConstants:
    KEY_ARGS = "args"
    KEY_NAME = "name"
    KEY_TYPE = "type"

    CONFIG_KEY_IP = "ip"
    CONFIG_KEY_PORT = "port"
    CONFIG_KEY_TOKEN = "token"

    MESSAGE_TYPE_EVENT = "event"
    MESSAGE_TYPE_INIT = "init"
    MESSAGE_TYPE_SHUTDOWN = "shutdown"
    MESSAGE_TYPE_TURN = "turn"

    CHANGE_TYPE_ADD = "a"
    CHANGE_TYPE_DEL = "d"
    CHANGE_TYPE_MOV = "m"
    CHANGE_TYPE_ALT = "c"

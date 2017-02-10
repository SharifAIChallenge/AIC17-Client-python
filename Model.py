from enum import Enum

import time

__author__ = 'RezaSoltani'

direction_x = [-1, 0, 1, 0]
direction_y = [0, 1, 0, -1]


class Move(Enum):
    turn_right = 0
    step_forward = 1
    turn_left = 2


class GameObject:
    def __init__(self, game_id, row, col):
        self.game_id = game_id
        self.row = row
        self.col = col


class Food(GameObject):
    def __init__(self, datum):
        GameObject.__init__(self, datum[0], datum[1], datum[2])


class Trash(GameObject):
    def __init__(self, datum):
        GameObject.__init__(self, datum[0], datum[1], datum[2])


class Net(GameObject):
    def __init__(self, datum):
        GameObject.__init__(self, datum[0], datum[1], datum[2])


class Fish(GameObject):
    def __init__(self, datum):
        GameObject.__init__(self, datum[0], datum[1], datum[2])
        self.dir = datum[3]
        self.color = datum[4]
        self.queen = datum[5]
        self.sick = datum[6]
        self.team = datum[7]

    def move(self, param):
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


class Teleport(GameObject):
    def __init__(self, datum):
        GameObject.__init__(self, datum[0], datum[1], datum[2])
        self.destination_id = datum[3]


class Map:
    def __init__(self, msg, team):
        self.team = team
        self.row_number = 0
        self.col_number = 0
        self.fishes = dict()
        self.foods = dict()
        self.trashes = dict()
        self.nets = dict()
        self.teleports = []
        self.game_map = [[]]
        self._handle_init_message(msg)

    def _handle_init_message(self, init_datum):
        self.row_number = init_datum[1][0]
        self.col_number = init_datum[1][1]

        for fish in init_datum[2]:
            fish_object = Fish(fish)
            self.fishes[fish_object.game_id] = fish_object

        for food in init_datum[3]:
            food_object = Food(food)
            self.foods[food_object.game_id] = food_object

        for trash in init_datum[4]:
            trash_object = Trash(trash)
            self.trashes[trash_object.game_id] = trash_object

        for net in init_datum[5]:
            net_object = Net(net)
            self.nets[net_object.game_id] = net_object

        for teleport in init_datum[6]:
            self.teleports.append(Teleport(teleport))

    def _handle_diff(self, diff):
        diff_type = diff[Constants.KEY_TYPE]
        diff_args_list = diff[Constants.KEY_ARGS]
        if diff_type == Constants.CHANGE_TYPE_ADD:
            for diff_args in diff_args_list:
                self._handle_add_diff(diff_args)
        elif diff_type == Constants.CHANGE_TYPE_DEL:
            for diff_args in diff_args_list:
                self._handle_delete_diff(diff_args)
        elif diff_type == Constants.CHANGE_TYPE_MOV:
            for diff_args in diff_args_list:
                item_game_id = diff_args[0]
                if item_game_id in self.fishes:
                    self.fishes[item_game_id].move(diff_args[1])
        else:
            for diff_args in diff_args_list:
                item_game_id = diff_args[0]
                if item_game_id in self.fishes:
                    self.fishes[item_game_id].row = diff_args[1]
                    self.fishes[item_game_id].col = diff_args[2]
                    self.fishes[item_game_id].color = diff_args[3]
                    self.fishes[item_game_id].sick = diff_args[4]

    def _handle_delete_diff(self, diff_args):
        item_game_id = diff_args[0]
        if item_game_id in self.fishes:
            self.fishes.pop(item_game_id, None)
        if item_game_id in self.foods:
            self.foods.pop(item_game_id, None)
        if item_game_id in self.trashes:
            self.trashes.pop(item_game_id, None)
        if item_game_id in self.nets:
            self.nets.pop(item_game_id, None)

    def _handle_add_diff(self, diff_args):
        entity_type = diff_args[1]
        item_game_id = diff_args[0]
        if entity_type == 0:
            self.fishes[item_game_id] = Fish(
                [diff_args[0], diff_args[2], diff_args[3], diff_args[4], diff_args[5], diff_args[6], 0, diff_args[7]])
        elif entity_type == 1:
            self.foods[item_game_id] = Food([diff_args[0], diff_args[2], diff_args[3]])
        elif entity_type == 2:
            self.trashes[item_game_id] = Trash([diff_args[0], diff_args[2], diff_args[3]])
        else:
            self.nets[item_game_id] = Net([diff_args[0], diff_args[2], diff_args[3]])

    def _rebuild_game_map(self):
        self.game_map = [[0 for x in range(self.col_number)] for y in range(self.row_number)]
        for fish in self.get_fishes_list():
            self.game_map[fish.row][fish.col] = fish
        for net in self.get_nets_list():
            self.game_map[net.row][net.col] = net
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

    def get_fishes_list(self):
        return self.fishes.values()

    def get_nets_list(self):
        return self.nets.values()

    def get_trashes_list(self):
        return self.trashes.values()

    def get_foods_list(self):
        return self.foods.values()

    def get_teleport_list(self):
        return self.teleports

    def get_game_2d_table(self):
        return self.game_map

    def get_my_fishes(self):
        return [fish for fish in self.fishes if fish.team == self.team]

    def get_opponent_fishes(self):
        return [fish for fish in self.fishes if fish.team != self.team]


class Constant:
    def __init__(self, msg):
        self._handle_init_message(msg)

    def _handle_init_message(self, msg):
        self.constants = msg
        self.turn_timeout = int(self.constants[0])
        self.food_prob = float(self.constants[1])
        self.trash_prob = float(self.constants[2])
        self.net_prob = float(self.constants[3])
        self.net_valid_time = float(self.constants[4])
        self.color_cost = float(self.constants[5])
        self.sick_cost = float(self.constants[6])
        self.update_cost = float(self.constants[7])
        self.det_move_cost = float(self.constants[8])
        self.kill_queen_score = float(self.constants[9])
        self.kill_both_queen_score = float(self.constants[10])
        self.kill_fish_score = float(self.constants[11])
        self.queen_collision_score = float(self.constants[12])
        self.queen_food_score = float(self.constants[13])
        self.sick_life_time = float(self.constants[14])
        self.power_ratio = float(self.constants[15])
        self.end_ratio = float(self.constants[16])
        self.disobey_num = float(self.constants[17])
        self.food_valid_time = float(self.constants[18])
        self.trash_valid_time = float(self.constants[19])
        self.total_turn_number = int(self.constants[20])

    def get_turn_timeout(self):
        return self.turn_timeout

    def get_food_prob(self):
        return self.food_prob

    def get_trash_prob(self):
        return self.trash_prob

    def get_net_prob(self):
        return self.net_prob

    def get_net_valid_time(self):
        return self.net_valid_time

    def get_color_cost(self):
        return self.color_cost

    def get_sick_cost(self):
        return self.sick_cost

    def get_update_cost(self):
        return self.update_cost

    def get_det_move_cost(self):
        return self.det_move_cost

    def get_kill_queen_score(self):
        return self.turn_timeout

    def get_kill_both_queen_score(self):
        return self.kill_both_queen_score

    def get_kill_fish_score(self):
        return self.kill_fish_score

    def get_queen_collision_score(self):
        return self.queen_collision_score

    def get_queen_food_score(self):
        return self.queen_food_score

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
        init_datum = msg[Constants.KEY_ARGS]
        self.my_game_id = int(init_datum[0])
        self.game_map = Map(init_datum, self.my_game_id)
        self.constants = Constant(init_datum[7])

    def _handle_turn_message(self, msg):
        self.turn_start_time = int(round(time.time() * 1000))

        current_datum = msg[Constants.KEY_ARGS]
        self.turn_number = int(current_datum[0])
        self.scores = current_datum[1]

        diffs = msg[Constants.KEY_ARGS][2]
        for diff in diffs:
            self.game_map._handle_diff(diff)
        self.game_map._rebuild_game_map()

    # Client APIs

    def get_turn_time_passed(self):
        return int(round(time.time() * 1000)) - self.turn_start_time

    def get_turn_remaining_time(self):
        return self.constants.turn_timeout - self.get_turn_time_passed()

    def get_current_turn_number(self):
        return self.turn_number

    def get_team_id(self):
        return self.my_game_id

    def get_my_score(self):
        return self.scores[0]

    def get_opponent_score(self):
        return self.scores[1]

    def change_strategy(self, color, front_right, front, front_left, new_strategy):
        self.queue.put(Event('s', [[color, front_right, front, front_left, new_strategy]]))

    def selective_move(self, fish, move):
        self.queue.put(Event('m', [[fish.game_id, move.value]]))

    def change_color(self, fish):
        self.queue.put(Event('c', [[fish.game_id, 1 - fish.color]]))

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


class Constants:
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

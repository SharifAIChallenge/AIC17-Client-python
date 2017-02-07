from aetypes import Enum

import time


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


class Teleport:
    # TODO: make init fix
    def __init__(self, datum):
        self.source_row = datum[0]
        self.source_col = datum[1]
        self.destination_row = datum[2]
        self.destination_col = datum[3]


class World:
    def __init__(self, queue):
        self.turn_timeout = None
        self.turn_start_time = None
        self.my_game_id = None
        self.row_number = None
        self.col_number = None
        self.fishes = dict()
        self.foods = dict()
        self.trashes = dict()
        self.nets = dict()
        self.teleports = []
        self.turn_number = 0
        self.scores = []
        self.constants = []
        self.queue = queue
        self.food_prob = float(0)
        self.trash_prob = float(0)
        self.net_prob = float(0)
        self.net_valid_time = float(0)
        self.color_cost = float(0)
        self.sick_cost = float(0)
        self.update_cost = float(0)
        self.det_move_cost = float(0)
        self.kill_queen_score = float(0)
        self.kill_both_queen_score = float(0)
        self.kill_fish_score = float(0)
        self.queen_collision_score = float(0)
        self.queen_food_score = float(0)
        self.sick_life_time = float(0)
        self.power_ratio = float(0)
        self.end_ratio = float(0)
        self.disobey_num = float(0)
        self.food_valid_time = float(0)
        self.trash_valid_time = float(0)

    def _handle_init_message(self, msg):
        init_datum = msg[Constants.KEY_ARGS]
        self.my_game_id = int(init_datum[0])
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

        self.constants = init_datum[7]
        self.turn_timeout = float(self.constants[0])
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

    def _handle_turn_message(self, msg):
        self.turn_start_time = int(round(time.time() * 1000))

        current_datum = msg[Constants.KEY_ARGS]
        self.turn_number = int(current_datum[0])
        self.scores = current_datum[1]

        diffs = msg[Constants.KEY_ARGS][2]
        for diff in diffs:
            self._handle_diff(diff)

    def _handle_diff(self, diff):
        diff_type = diff[Constants.KEY_TYPE]
        diff_args = diff[Constants.KEY_ARGS]
        if diff_type == Constants.CHANGE_TYPE_ADD:
            self._handle_add_diff(diff_args)
        elif diff_type == Constants.CHANGE_TYPE_DEL:
            self._handle_delete_diff(diff_args)
        elif diff_type == Constants.CHANGE_TYPE_MOV:
            item_game_id = diff_args[0]
            if item_game_id in self.fishes:
                self.fishes[item_game_id].move(diff_args[1])
        else:
            item_game_id = diff_args[0]
            if item_game_id in self.fishes:
                self.fishes[item_game_id].color = diff_args[1]
                self.fishes[item_game_id].sick = diff_args[2]

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
            self.fishes[item_game_id] = Food([diff_args[0], diff_args[2], diff_args[3]])
        elif entity_type == 2:
            self.trashes[item_game_id] = Trash([diff_args[0], diff_args[2], diff_args[3]])
        else:
            self.nets[item_game_id] = Net([diff_args[0], diff_args[2], diff_args[3]])

    # Client APIs

    def get_turn_time_passed(self):
        return int(round(time.time() * 1000)) - self.turn_start_time

    def get_turn_remaining_time(self):
        return self.turn_timeout - self.get_turn_time_passed()

    def change_strategy(self, color, front_right, front, front_left, new_strategy):
        self.queue.put(Event('s', [color, front_right, front, front_left, new_strategy]))

    def selective_move(self, fish, move):
        self.queue.put(Event('m', [fish.game_id, move]))

    def change_color(self, fish):
        self.queue.put(Event('c', [fish.game_id, 1 - fish.color]))

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

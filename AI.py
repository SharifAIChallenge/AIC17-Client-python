from random import randint

from Model import Move, BeetleType

__author__ = 'RezaS'


class AI:
    def do_turn(self, world):
        beetles = world.get_map().get_beetles_list()
        for beetle in beetles:
            if randint(0, 100) % 3 == 0:
                world.change_type(beetle, BeetleType.HIGH.value)
            elif randint(0, 100) % 3 == 1:
                world.change_strategy(randint(0, 100) % 2, randint(0, 100) % 3, randint(0, 100) % 2,
                                      randint(0, 100) % 3, Move.step_forward)
            else:
                if randint(0, 100) % 3 == 0:
                    world.deterministic_move(beetle, Move.step_forward)
                elif randint(0, 100) % 3 == 1:
                    world.deterministic_move(beetle, Move.turn_left)
                else:
                    world.deterministic_move(beetle, Move.turn_right)
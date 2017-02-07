from random import randint

from Model import Move

__author__ = 'AmirHS'


class AI():
    def do_turn(self, world):
        fishes = world.fishes
        for fish in fishes:
            if randint(0, 100) % 3 == 0:
                world.change_color(fish)
            elif randint(0, 100) % 3 == 1:
                world.change_strategy(randint(0, 100) % 2, randint(0, 100) % 3, randint(0, 100) % 2,
                                      randint(0, 100) % 3, randint(0, 100) % 3)
            else:
                if randint(0, 100) % 3 == 0:
                    world.selective_move(fish, Move.step_forward)
                elif randint(0, 100) % 3 == 1:
                    world.selective_move(fish, Move.turn_left)
                else:
                    world.selective_move(fish, Move.turn_right)
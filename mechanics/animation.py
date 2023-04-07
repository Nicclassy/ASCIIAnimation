import os
import signal
import time
import threading
from typing import Callable, Optional

from getkey import getkey, keys

from mechanics.movement.position import Position
from mechanics.movement.vectors import Vector, UnitVector, VectorStream
from mechanics.sprites.gamesprites import PlayerSprite
from mechanics.terrain import Terrain


class Animator:

    def __init__(self, terrain: Terrain):
        self._vector_stream = VectorStream()
        self._player_sprite = terrain.player_sprite
        self._terrain = terrain
        self._terrain_thread_function = self.terrain_output
        self._player_thread_function = self.player_movement_input
        self._terrain_thread = None
        self._player_thread = None
        self._time_elapsed = float()

    @staticmethod
    def hide_cursor():
        print('\033[?25l')

    @staticmethod
    def unhide_cursor():
        print("\033[?25h")

    @staticmethod
    def exit():
        Animator.unhide_cursor()
        os.kill(os.getpid(), signal.SIGTERM)

    def update_terrain(self):
        self._terrain.update_sprites(self._time_elapsed)
        self._terrain.move_timed_sprites(time.perf_counter())
        self._terrain.draw_sprites()
        self._terrain.move_player_sprite(self._vector_stream.get_vector())
        self._terrain.draw_player_sprite()
        self._terrain.sleep_updateable_sprites()

    def terrain_output(self):
        self.hide_cursor()
        start_time = time.perf_counter()
        while 1:
            self._time_elapsed = time.perf_counter() - start_time
            self.update_terrain()
            os.system("clear")
            print(self._terrain)
            self._vector_stream.reset()
            self._terrain.reset()
            time.sleep(0.1)

    def player_movement_input(self):
        while 1:
            match getkey():
                case keys.UP | "w":
                    vector = UnitVector.UP
                case keys.DOWN | "s":
                    vector = UnitVector.DOWN
                case keys.RIGHT | "d":
                    vector = UnitVector.RIGHT * 2
                case keys.LEFT | "a":
                    vector = UnitVector.LEFT * 2
                case _:
                    vector = Vector.ZERO
            self._vector_stream.set_vector(vector)

    def set_threads(self, player_thread: Optional[Callable] = None, terrain_thread: Optional[Callable] = None):
        self._player_thread_function = player_thread or self._player_thread_function
        self._terrain_thread_function = terrain_thread or self._terrain_thread_function

    def run(self):
        self._terrain_thread = threading.Thread(target=self._terrain_thread_function)
        self._player_thread = threading.Thread(target=self._player_thread_function)

        self._terrain_thread.start()
        self._player_thread.start()


if __name__ == "__main__":
    ps = PlayerSprite([["/", "–", "\\"], ["|", "0", "|"], ["\\", "–", "/"]], Position(0, 12))
    # ter = Terrain("bxl.json", ps)
    ter = Terrain("court.json", ps)
    # ps.paint({"fore": {"blue": ["–", "|"], "0": "red"}}, fore_all="green")
    # ter.sprites.append(LoadingSprite(Position(4, 4)))
    # ter.add_sprite(LoadingSprite(Position(4, 4), update_interval=0.2), position_below=3)
    # ter.sprites.append(TimerSprite(Position(3, 2), 0, 5))
    # ter.sprites.append(LoadingSprite(Position(8, 8)))
    # ter.sprites.append(EllipsisLoadingSprite(Position(5, 1)))
    # cs = CharacterStreamSprite("Hello.\nIdk if this works.\nBye.", position=Position(0, 0))
    # ter.sprites.append(cs)

    from mechanics.sprites.projectile import StandardProjectileSprite

    ball = StandardProjectileSprite([["O"]], velocity=5, angle=45, gravity=1, projection_quadrant=3,
                                    starting_position=Position(0, 0))
    for t in range(16):
        print((t, ball.get_position_at_time(t, ter.height, ter.width)[0]))
    # quit()
    ter.sprites.append(ball)

    # for i in range(1, 5):
    #     #i: Literal[1, 2, 3, 4]
    #     from mechanics.sprites.projectile import StandardProjectileSprite
    #     ter.sprites.append(StandardProjectileSprite([[str(i)]], velocity=3.5, angle=45, gravity=1,
    #                                                 projection_quadrant=i, starting_position=(0, 0),
    #                                                 truncation_factor=(1, 1)))
    # p = ProjectileSprite([["•"]], velocity=3.5, angle=45, gravity=1, projection_quadrant=2)
    #
    # print(p.get_horizontal_range())
    # print(p.get_max_height())
    #
    # for t in range(16):
    #     # print()
    #     print(p.get_position_at_time(t, ter, return_float=True)[::-1])

    animator = Animator(ter)
    animator.run()

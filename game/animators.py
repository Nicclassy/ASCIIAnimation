import os
import time
import threading
import random
from typing import Callable
from functools import wraps

from getkey import getkey, keys

from text.colours import FORE_COLOUR_MAPPING
from mechanics.constants import BLANK_CHARACTER
from mechanics.maths.algebra import ExponentialEquation
from mechanics.movement.position import Position, RelativePosition
from mechanics.movement.vectors import UnitVector, Vector
from mechanics.sprites.gamesprites import (
    PlayerSprite, BasketballSprite, StaticSprite, TimerSprite, DiagonalSprite, ShieldSprite, ArrowSprite,
    HealthBarSprite, HealthPlayerSprite, CharacterStreamSprite, BallSprite, EllipsisLoadingSprite,
    LoadingSprite
)
from mechanics.animation import Animator
from mechanics.terrain import Terrain
from text.character import ModifiedCharacter


class BasketballGameAnimator(Animator):

    def __init__(self):
        hoop_position = Position(11, 47)
        terrain = Terrain("court.json", PlayerSprite("shooter.json", Position(14, 0)),
                          ground_characters={"⎻"}, uncollidable_characters={"⎻"})
        terrain.player_sprite.paint({"fore": {"O": "red"}})
        terrain.sprites.append(StaticSprite("hoop.json", hoop_position))
        self.__pressed_key = None
        self.__ball_position = RelativePosition(1, 3)
        self.__ball_character = "O"
        self.__time_of_hoop_scoring = None
        self.__ball_sprite: BasketballSprite | None = None
        self.__in_hoop_position = RelativePosition(1, 1).normalize_wrt_sprite(hoop_position)
        # if the ball goes in any of these positions, it counts as going in the hoop
        self.__permissible_positions = {
            RelativePosition.ORIGIN.normalize_wrt_sprite(hoop_position),
            RelativePosition(0, 1).normalize_wrt_sprite(hoop_position),
            self.__in_hoop_position,
        }
        super().__init__(terrain)
        self.__running = True
        self.__initial_press = False
        self.__thrown_ball = False
        self.__ball_release = True
        self.__hoop_scored = None

    @property
    def running(self) -> bool:
        return self.__running

    def shoot_ball(self, start_time: float):
        while self.__pressed_key == "r":
            pass
        y, x = self.__ball_position
        starting_position = Position(
            self._terrain.height - self._terrain.player_sprite.position[0],
            self._terrain.player_sprite.position[1]
        )
        # Position will move downwards because Q3 is measured from the bottom,
        # hence the adding of the up unit vector
        starting_position += self.__ball_position + UnitVector.UP * 2
        angle = ExponentialEquation(limit=45).get_value_at_time(time.perf_counter() - start_time)
        self.__ball_sprite = BasketballSprite([[self.__ball_character]], velocity=angle // 6, angle=angle,
                                              gravity=1, projection_quadrant=3,
                                              starting_position=starting_position)
        self.__ball_sprite.paint(fore_all="red")
        self.__thrown_ball = True
        self._terrain.sprites.append(self.__ball_sprite)
        self._terrain.player_sprite[y][x] = BLANK_CHARACTER

    def terrain_output(self):
        self.hide_cursor()
        start_time = time.perf_counter()
        while self.__running:
            if self.__hoop_scored and self.__time_of_hoop_scoring is None:
                self.__time_of_hoop_scoring = time.perf_counter()
            if type(self.__time_of_hoop_scoring) is float and time.perf_counter() - self.__time_of_hoop_scoring >= 2:
                time.sleep(2)
                self.__running = False
                self.exit()
            self._time_elapsed = time.perf_counter() - start_time
            self.update_terrain()
            os.system("clear")
            print(self._terrain)
            self._vector_stream.reset()
            self._terrain.reset()
            if isinstance(self.__ball_sprite, BasketballSprite):
                if not self.__ball_sprite.alive:
                    self.__ball_sprite = None
                    self.__ball_release = True
                    self.__thrown_ball = False
                    self.__initial_press = False
                    y, x = self.__ball_position
                    self._terrain.player_sprite[y][x] = ModifiedCharacter(self.__ball_character, fore_colour_name="RED")
                elif self.__ball_sprite.position in self.__permissible_positions and not self.__hoop_scored:
                    ball_in_hoop = StaticSprite([[self.__ball_character]], self.__in_hoop_position)
                    ball_in_hoop.paint(fore_all="red")
                    self._terrain.sprites.append(ball_in_hoop)
                    self._terrain.sprites.remove(self.__ball_sprite)
                    self.__hoop_scored = True
                    self.__ball_sprite = None
            time.sleep(0.1)

    def player_movement_input(self):
        angle_start_time = float()
        while self.__running:
            self.__ball_release = True
            vector = Vector.ZERO
            self.__pressed_key = getkey()
            match self.__pressed_key:
                case "r":
                    self.__ball_release = False
                    if not self.__initial_press:
                        self.__initial_press = True
                        angle_start_time = time.perf_counter()
                case keys.RIGHT | "d":
                    vector = UnitVector.RIGHT
                case keys.LEFT | "a":
                    vector = UnitVector.LEFT
            if self.__ball_release and self.__initial_press and not self.__thrown_ball and not self.__hoop_scored:
                ball_shoot_thread = threading.Thread(target=self.shoot_ball, args=(angle_start_time,))
                ball_shoot_thread.start()
            self._vector_stream.set_vector(vector)


class DodgerGameAnimator(Animator):

    def __init__(self):
        self.__starting_player_health = 6
        player_sprite = HealthPlayerSprite([["(", "Ο", ")"]], Position(11, 20), self.__starting_player_health)
        player_sprite.paint({"fore": {"cyan": ["(", ")"], "Ο": "red"}})
        terrain = Terrain("arena.json", player_sprite, uncollidable_characters={"│", "—", "∆"})
        terrain.paint({"fore": {"magenta": ["∆", "•"], "lightblack": ["│", "—"]}})
        terrain.sprites.append(EllipsisLoadingSprite(Position(2, 17), length=5, update_interval=0.57))
        terrain.sprites.append(LoadingSprite(Position(2, 16), update_interval=0.35))
        terrain.sprites.append(LoadingSprite(Position(2, 22), update_interval=0.74))
        self.__colours = list(set(FORE_COLOUR_MAPPING.keys()) - {"RESET", "LIGHTBLACK"})
        self.__game_duration = 45
        self.__game_over_sprite: CharacterStreamSprite | None = None
        self.__last_ten_seconds = False
        self.__frozen = False
        self.__game_won = False
        self.__running = True
        self.__timer_sprite = TimerSprite(Position(1, 33), seconds=self.__game_duration)
        self.__health_bar = HealthBarSprite(self.__starting_player_health, Position(1, 1), player_sprite)
        self.__spawn_interval = 5
        self.__spawn_distance_from_player = 7
        self.__starting_shields = 6
        self.__min_projectile_x, self.__max_projectile_x = 1, terrain.width - 2
        self.__min_projectile_y, self.__max_projectile_y = 5, terrain.height - 2
        self.__sprite_quantities = {
            2: 3,
            4: 4,
            6: 5,
        }
        self.__sprite_types = {
            2: DiagonalSprite,
            4: ArrowSprite,
            6: BallSprite,
        }
        terrain.sprites.append(self.__timer_sprite)
        terrain.sprites.append(self.__health_bar)
        super().__init__(terrain)

    @property
    def running(self) -> bool:
        return self.__running

    def get_random_position(self) -> Position:
        unchoosable_coordinates = self._terrain.get_sprite_coverage()
        random_position = Position(
            random.randint(self.__min_projectile_y, self.__max_projectile_y),
            random.randint(self.__min_projectile_x, self.__max_projectile_x),
        )
        magnitude_from_player = abs(Vector(*(random_position - self._terrain.player_sprite.position)))
        outside_proximity = magnitude_from_player > self.__spawn_distance_from_player
        while random_position in unchoosable_coordinates and outside_proximity:
            random_position = Position(
                random.randint(self.__min_projectile_y, self.__max_projectile_y),
                random.randint(self.__min_projectile_x, self.__max_projectile_x),
            )
            magnitude_from_player = abs(Vector(*(random_position - self._terrain.player_sprite.position)))
            outside_proximity = magnitude_from_player > self.__spawn_distance_from_player
        return random_position

    def spawn_random_projectiles(self, intervals_passed: int, num: int = 1):
        for _ in range(num):
            if self.__game_duration - self.__timer_sprite.get_seconds_passed() <= 10:
                self._terrain.paint({"fore": {random.choice(self.__colours): ["∆", "•"]}})
                self.__health_bar.paint({"back": {" ": random.choice(self.__colours)}})
                colour = random.choice(self.__colours)
                if not self.__last_ten_seconds:
                    self.__sprite_quantities[2] += 2
                    self.__sprite_quantities[4] += 2
                    self.__sprite_quantities[6] += 2
                self.__last_ten_seconds = True
            else:
                colour = None
            match intervals_passed:
                case 2:
                    gradient = (random.randint(30, 50) if intervals_passed >= 4 else random.randint(10, 30)) / 10
                    gradient *= random.choice((-1, 1))
                    projection_quadrant = random.randint(1, 4)
                    projectile = DiagonalSprite(
                        [["✯"]], projection_quadrant, gradient, self.get_random_position(),  # type: ignore
                    )
                    projectile.paint(fore_all=colour or "lightyellow")
                    self._terrain.sprites.append(projectile)
                case 4:
                    if intervals_passed >= 7:
                        gradient = random.randint(600, 750) / 10
                    else:
                        gradient = random.randint(500, 540) / 10
                    projection_quadrant = random.randint(1, 2)
                    sprite_array = [["⇉", "⇉"]] if projection_quadrant == 2 else [["⇇", "⇇"]]
                    starting_position = Position(
                        random.randint(self.__min_projectile_y, self.__max_projectile_y),
                        random.choice([self.__min_projectile_x, self.__max_projectile_x])
                    )
                    projectile = ArrowSprite(
                        sprite_array, projection_quadrant, gradient, starting_position  # type: ignore
                    )
                    projectile.paint(fore_all=colour or "green")
                    self._terrain.sprites.append(projectile)
                case 6:
                    starting_position = Position(
                        random.randint(self.__min_projectile_y, self.__max_projectile_y),
                        random.choice([self.__min_projectile_x, self.__max_projectile_x])
                    )
                    projectile = BallSprite(
                        [["●"]], random.randint(3, 10), random.randint(1, 45), random.randint(1, 3),
                        random.randint(1, 2), starting_position  # type: ignore
                    )
                    projectile.paint(fore_all=colour or "red")
                    self._terrain.sprites.append(projectile)

    def spawn_shields(self, quantity: int):
        for sprite in self._terrain.sprites:
            if type(sprite) is ShieldSprite:
                self._terrain.sprites.remove(sprite)
        for _ in range(quantity if quantity > 0 else 0):
            position = self.get_random_position()
            character = random.choice(["━", "║", "☲", "☷", "☵", "☰"])
            self._terrain.sprites.append(ShieldSprite(character, position))

    def terrain_output(self):
        self.hide_cursor()
        start_time = time.perf_counter()
        intervals = 1
        self.spawn_shields(self.__starting_shields - intervals + 1)
        while self.__running:
            self._time_elapsed = time.perf_counter() - start_time
            self.__health_bar.set_health()
            if not self.__frozen:
                if self.__timer_sprite.get_seconds_passed() // (self.__spawn_interval * intervals) == 1:
                    if (sprite_quantities := self.__sprite_quantities.get(intervals)) is not None:
                        self.spawn_random_projectiles(intervals, num=sprite_quantities)
                    self.spawn_shields(self.__starting_shields - intervals + 1)
                    if intervals >= 4:
                        self.__sprite_quantities[4] += 1
                    if intervals >= 2:
                        self.__sprite_quantities[2] += 1
                    if intervals > 6:
                        self.__sprite_quantities[6] += 2
                    intervals += 1
                for sprite_num, max_amount in self.__sprite_quantities.items():
                    sprite_type = self.__sprite_types[sprite_num]
                    amount = sum(map(lambda sprite: type(sprite) is sprite_type, self._terrain.sprites))
                    if amount < max_amount and intervals >= sprite_num:
                        self.spawn_random_projectiles(sprite_num, num=max_amount - amount)
            self._player_sprite: HealthPlayerSprite
            if self._player_sprite.health <= 0 and not self.__frozen:
                for terrain_sprite in self._terrain.sprites:
                    if isinstance(terrain_sprite, (LoadingSprite, EllipsisLoadingSprite)):
                        self._terrain.remove_sprite(terrain_sprite)
                self._terrain.remove_sprite(self.__timer_sprite)
                self._terrain.paint({"fore": {"black": ["∆", "•"]}})
                self.__game_over_sprite = CharacterStreamSprite("Game over!", Position(2, 15))
                self._terrain.sprites.append(self.__game_over_sprite)
                self.__frozen = True
            if not self.__frozen:
                self.update_terrain()
            else:
                self._terrain.update_sprites(self._time_elapsed)
                self._terrain.draw_sprites()
            os.system("clear")
            print(self._terrain)
            self._vector_stream.reset()
            sprite_is_character_stream = type(self.__game_over_sprite) is CharacterStreamSprite
            if self.__frozen and sprite_is_character_stream and self.__game_over_sprite.exhausted:
                time.sleep(4)
                self.__running = False
                self.exit()
            if not self.__frozen:
                self._terrain.reset()
            if self.__timer_sprite.get_seconds_passed() == self.__game_duration and not self.__frozen:
                time.sleep(4)
                self.__running = False
            time.sleep(0.1)

    def player_movement_input(self):
        while self.__running:
            vector = Vector.ZERO
            match getkey():
                case keys.UP | "w":
                    vector = UnitVector.UP
                case keys.DOWN | "s":
                    vector = UnitVector.DOWN
                case keys.RIGHT | "d":
                    vector = UnitVector.RIGHT
                case keys.LEFT | "a":
                    vector = UnitVector.LEFT
                case "c":
                    self.__running = False
            self._vector_stream.set_vector(vector)


class PreDodgerGameAnimator(Animator):

    def __init__(self):
        terrain = Terrain("line_terrain.json", PlayerSprite([[BLANK_CHARACTER]], Position.ORIGIN))
        path = "played.txt" if __name__ == "__main__" else os.path.realpath(os.path.join("game", "played.txt"))
        played_before = eval(open(path).read() or str(False), {}, {})
        if played_before:
            starting_text = "Welcome back. You're here for another chance, aren't you?\nLet's get straight into it."
        else:
            starting_text = """Welcome Challenger. You will play two games to prove your worth.
Complete them both and you will be a victor.\nYou will need for them are the arrow keys.
The second game requires the R key.\nGood luck."""
        self.__starting_message = CharacterStreamSprite(starting_text, Position(1, 0))
        self.__second_message = CharacterStreamSprite(
            "In this game, you must survive for 45 seconds.\n"
            "All four arrow keys may be used for movement.\n"
            "Use the randomly spawning shields to protect you.\n",
            Position(1, 0)
        )
        terrain.sprites.append(self.__starting_message)
        terrain.sprites.append(EllipsisLoadingSprite(Position(23, 66)))
        terrain.sprites.append(LoadingSprite(Position(23, 65)))
        super().__init__(terrain)
        self.__running = True
        self.__start_second_message = False

    @property
    def running(self) -> bool:
        return self.__running

    def terrain_output(self):
        self.hide_cursor()
        start_time = time.perf_counter()
        while self.__running:
            self._time_elapsed = time.perf_counter() - start_time
            if self.__starting_message.exhausted and not self.__start_second_message:
                self._terrain.sprites.clear()
                self._terrain.sprites.append(self.__second_message)
                self._terrain.paint(fore_all="lightblack")
                for quadrant in range(1, 5):
                    position = RelativePosition.ORIGIN.normalize(
                        quadrant, self._terrain.height, self._terrain.width  # type: ignore
                    )
                    self._terrain.set_position_to(position, "∆")
                    self._terrain.paint({"fore": {"∆": "black"}})
                time.sleep(2)
                self.__start_second_message = True
            if self.__second_message.exhausted:
                time.sleep(3)
                self.__running = False
                with open("played.txt", "w") as file:
                    file.write("True")
            self.update_terrain()
            os.system("clear")
            print(self._terrain)
            self._terrain.reset()
            time.sleep(0.01)

    def player_movement_input(self):
        match getkey():
            case "c" | "n":
                self.__running = False


class PreBasketballGameAnimator(Animator):

    def __init__(self):
        terrain = Terrain("line_terrain.json", PlayerSprite([[BLANK_CHARACTER]], Position.ORIGIN))
        self.__message = CharacterStreamSprite(
            "Well done on completing the first game.\n"
            "In this game you must score 1 basket.\n"
            "Use the left and right arrow keys to move.\n"
            "Hold the R key to increase the angle at which the ball is thrown.\n"
            "Have fun.", Position(1, 0)
        )
        terrain.sprites.append(self.__message)
        terrain.sprites.append(EllipsisLoadingSprite(Position(23, 66), update_interval=0.71))
        terrain.sprites.append(LoadingSprite(Position(23, 65), update_interval=0.67))
        self.__running = True
        super().__init__(terrain)

    @property
    def running(self) -> bool:
        return self.__running

    def terrain_output(self):
        self.hide_cursor()
        start_time = time.perf_counter()
        while self.__running:
            self._time_elapsed = time.perf_counter() - start_time
            if self.__message.exhausted:
                self.__running = False
            self.update_terrain()
            os.system("clear")
            print(self._terrain)
            self._terrain.reset()
            time.sleep(0.01)

    def player_movement_input(self):
        match getkey():
            case "c" | "n":
                self.__running = False


def terminal_output(function: Callable):
    @wraps(function)
    def wrapper():
        try:
            os.get_terminal_size()
        except OSError:
            error_message = "You are not running this program on a terminal-based console. " \
                            "Please use a terminal based console before running this program."
            raise OSError(error_message) from None
        else:
            os.environ["TERM"] = "xterm-256color"
            os.environ["PYTHONUNBUFFERED"] = "1"
            function()
    return wrapper


animators = iter((PreDodgerGameAnimator, DodgerGameAnimator, PreBasketballGameAnimator, BasketballGameAnimator))

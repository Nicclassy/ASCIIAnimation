import time

from mechanics.types import Numeric


class Timer:

    def __init__(self, minutes: Numeric = 0, seconds: Numeric = 0):
        assert seconds or minutes
        self.__seconds_to_count = minutes * 60 + seconds + 1
        self.__start_time = time.perf_counter()

    def __call__(self) -> list[str, str]:
        minutes, seconds = self.get_current_time()
        display_values = [str(minutes).zfill(2), str(seconds).zfill(2)]
        return display_values

    @property
    def seconds_to_count(self):
        return self.__seconds_to_count

    def get_current_time(self) -> tuple[int, int]:
        difference = self.__seconds_to_count - (time.perf_counter() - self.__start_time)
        minutes, seconds = divmod(difference, 60)
        return int(minutes), int(seconds)

    def reset(self):
        self.__start_time = time.perf_counter()

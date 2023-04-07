from typing import List, Optional

import pygame

from constants import *


class _CoordinateGenerator:

    def __init__(self, *, max_y: int, max_x: int, reverse: bool = False):
        self.coordinates = [(x, y) if reverse else (y, x) for y in range(max_y) for x in range(max_x)]
        self.position = 0
        self.length = len(self.coordinates)

    def next(self, return_old: bool = True):
        if return_old:
            old_position = self.position
            self.position = (self.position + 1) % self.length
            return self.coordinates[old_position]
        else:
            self.position = (self.position + 1) % self.length
            return self.coordinates[self.position]

    def previous(self, return_old: bool = True):
        if return_old:
            old_position = self.position
            self.position = (self.position - 1) % self.length
            return self.coordinates[old_position]
        else:
            self.position = (self.position - 1) % self.length
            return self.coordinates[self.position]


def draw_text(screen: pygame.Surface, text: str, position: tuple, size: int = DEFAULT_TEXT_SIZE):
    if not text.isprintable():
        text = ""
    font = pygame.font.Font(pygame.font.get_default_font(), size)
    text_surface = font.render(text, True, TEXT_COLOUR)
    text_rect = text_surface.get_rect()
    text_rect.center = position
    screen.blit(text_surface, text_rect)


class Box:

    def __init__(self, name: str, left_side_margin: int, right_side_margin: int, upper_margin: int,
                 lower_margin: int, list_height: int, list_width: int, display_width: int,
                 display_height: int, line_colour: tuple, line_thickness: int = DEFAULT_BOX_LINE_THICKNESS,
                 character_list: Optional[list] = None):
        self.name = name
        self.left_side_margin = left_side_margin
        self.right_side_margin = right_side_margin
        self.upper_margin = upper_margin
        self.lower_margin = lower_margin
        self.list_height = list_height
        self.list_width = list_width
        self.list_display_width = display_width - left_side_margin - right_side_margin
        self.list_display_height = display_height - lower_margin - upper_margin
        self.display_width = display_width
        self.display_height = display_height
        self.line_color = line_colour
        self.line_thickness = line_thickness
        self.character_list = character_list or [[NO_DATA] * list_width for _ in range(list_height)]
        self.coordinate_generator = _CoordinateGenerator(max_y=self.list_height, max_x=self.list_width)
        self.box_top = upper_margin
        self.box_bottom = display_height - lower_margin
        self.box_left = left_side_margin
        self.box_right = display_width - left_side_margin
        self.cell_width = self.list_display_width / list_width
        self.cell_height = self.list_display_height / list_height

    def __getitem__(self, index: int) -> list:
        return self.character_list[index]

    def __len__(self) -> int:
        return self.list_height

    def draw_lines(self, screen: pygame.Surface):
        for y in range(1, self.list_height + 1):
            for x in range(self.list_width + 1):
                start_pos = x * (
                    self.list_display_width) // self.list_width + self.left_side_margin, self.upper_margin
                end_pos = x * (
                    self.list_display_width) // self.list_width + self.left_side_margin, self.display_height - self.lower_margin
                pygame.draw.line(screen, self.line_color, start_pos, end_pos, self.line_thickness)
        for y in range(self.list_height + 1):
            for x in range(1, self.list_width + 1):
                start_pos = self.left_side_margin, y * self.cell_height + self.upper_margin
                end_pos = self.display_width - self.right_side_margin, y * self.cell_height + self.upper_margin
                pygame.draw.line(screen, self.line_color, start_pos, end_pos, self.line_thickness)

    def draw_characters(self, screen: pygame.Surface):
        characters = set(((y, x), self.character_list[y][x])
                         for y in range(self.list_height) for x in range(self.list_width)
                         if self.character_list[y][x] != NO_DATA
                         )
        for (y, x), character in characters:
            draw_text(screen, character, self.convert_coordinates_to_mouse_position((x, y)))

    def draw_rectangles(self, screen: pygame.Surface):
        for y in range(self.list_height):
            for x in range(self.list_width):
                top = self.upper_margin + y * self.cell_height
                left = self.left_side_margin + x * self.cell_width
                rect = pygame.rect.Rect(left, top, self.cell_width, self.cell_height)
                pygame.draw.rect(screen, CELL_COLOUR, rect)

    def convert_mouse_position_to_coordinates(self, mouse_position: tuple) -> tuple:
        mouse_x, mouse_y = mouse_position
        # Position relative to the top/bottom divided by the length/width of the box,
        # that division is how many boxes long/wide the cursor's position is and hence its position
        x = (mouse_x - self.left_side_margin) // (self.list_display_width // self.list_width)
        y = (mouse_y - self.upper_margin) // (self.list_display_height // self.list_height)
        return x, y

    def convert_coordinates_to_mouse_position(self, coordinates: tuple) -> tuple:
        x, y = coordinates
        mouse_x = self.left_side_margin + x * self.cell_width + self.cell_width // 2
        mouse_y = self.upper_margin + y * self.cell_height + self.cell_height // 2
        return mouse_x, mouse_y

    def position_in_box(self, mouse_position: tuple) -> tuple:
        mouse_x, mouse_y = mouse_position
        return self.box_left <= mouse_x <= self.box_right and self.box_top <= mouse_y <= self.box_bottom

    def on_intersect(self, screen: pygame.Surface, position: tuple, mouse_event: int,
                     character: Optional[str] = None):
        pass

    def draw_features(self, screen: pygame.Surface):
        pass


class CharacterBox(Box):

    def __init__(self, name: str, left_side_margin: int, right_side_margin: int, upper_margin: int,
                 lower_margin: int, list_height: int, list_width: int, display_width: int,
                 display_height: int, line_colour: tuple, line_thickness: int = DEFAULT_BOX_LINE_THICKNESS,
                 character_list: Optional[list] = None):
        super().__init__(name, left_side_margin, right_side_margin, upper_margin, lower_margin, list_height, list_width,
                         display_width, display_height, line_colour, line_thickness, character_list)
        self.selected_position = (0, 0)
        self.highlight_coordinates = _CoordinateGenerator(max_x=list_width, max_y=list_height, reverse=True)

    def on_intersect(self, screen: pygame.Surface, position: tuple, mouse_event: int,
                     character: Optional[str] = None):
        self.highlight_coordinates.position = self.highlight_coordinates.coordinates.index(position)
        self.selected_position = position

    def draw_features(self, screen: pygame.Surface):
        self.draw_rectangles(screen)
        self.draw_lines(screen)
        self.draw_characters(screen)
        self.highlight_selected_position(screen)

    def highlight_selected_position(self, screen: pygame.Surface):
        start_x, start_y = self.left_side_margin + self.cell_width * self.selected_position[0], \
                           self.upper_margin + self.cell_height * self.selected_position[1]
        end_x, end_y = start_x + self.cell_width, start_y + self.cell_height
        pygame.draw.line(screen, HIGHLIGHT_COLOUR, (start_x, start_y), (end_x, start_y), self.line_thickness + 3)
        pygame.draw.line(screen, HIGHLIGHT_COLOUR, (start_x, end_y), (end_x, end_y), self.line_thickness + 3)
        pygame.draw.line(screen, HIGHLIGHT_COLOUR, (start_x, start_y), (start_x, end_y), self.line_thickness + 3)
        pygame.draw.line(screen, HIGHLIGHT_COLOUR, (end_x, start_y), (end_x, end_y), self.line_thickness + 3)

    def add_character(self, character: str, add_on_highlight: bool = False):
        if add_on_highlight:
            highlight_x, highlight_y = self.selected_position
            self.character_list[highlight_y][highlight_x] = character
        else:
            list_y, list_x = self.coordinate_generator.next()
            self.character_list[list_y][list_x] = character

    def get_selected_character(self) -> str:
        x, y = self.selected_position
        return self.character_list[y][x]

    def move_highlight_left(self):
        self.selected_position = self.highlight_coordinates.previous(return_old=False)

    def move_highlight_right(self):
        self.selected_position = self.highlight_coordinates.next(return_old=False)

    def move_highlight_down(self):
        x, y = self.selected_position
        y = (y + 1) % len(self.character_list)
        self.selected_position = (x, y)
        self.highlight_coordinates.position = self.highlight_coordinates.coordinates.index((x, y))

    def move_highlight_up(self):
        x, y = self.selected_position
        y = (y - 1) % len(self.character_list)
        self.selected_position = (x, y)
        self.highlight_coordinates.position = self.highlight_coordinates.coordinates.index((x, y))


class ArtBox(Box):

    def __init__(self, name: str, left_side_margin: int, right_side_margin: int, upper_margin: int,
                 lower_margin: int, list_height: int, list_width: int, display_width: int,
                 display_height: int, line_colour: tuple, line_thickness: int = DEFAULT_BOX_LINE_THICKNESS,
                 character_list: Optional[list] = None):
        super().__init__(name, left_side_margin, right_side_margin, upper_margin, lower_margin, list_height, list_width,
                         display_width, display_height, line_colour, line_thickness, character_list)
        self.selected_position = (0, 0)

    def on_intersect(self, screen: pygame.Surface, position: tuple, mouse_event: int,
                     character: Optional[str] = None):
        x, y = position
        if self.position_in_box(self.convert_coordinates_to_mouse_position(position)):
            if mouse_event == 1:
                self.character_list[y][x] = character
            elif mouse_event == 3:
                self.character_list[y][x] = NO_DATA

    def fill_with_character(self, character: str, fill: str = "row"):
        mouse_pos = pygame.mouse.get_pos()
        x, y = self.convert_mouse_position_to_coordinates(mouse_pos)
        if self.position_in_box(self.convert_coordinates_to_mouse_position((x, y))):
            if fill == "row":
                self.character_list[y] = [character] * self.list_width
            elif fill == "column":
                for row in range(self.list_height):
                    self.character_list[row][x] = character

    def draw_hover(self, screen: pygame.Surface):
        coordinate_in_box = self.position_in_box(self.convert_coordinates_to_mouse_position(
            self.convert_mouse_position_to_coordinates(mouse_position := pygame.mouse.get_pos())
        ))
        if coordinate_in_box:
            x, y = self.convert_mouse_position_to_coordinates(mouse_position)
            top = self.upper_margin + y * self.cell_height
            left = self.left_side_margin + x * self.cell_width
            surface_region = left, top, self.cell_width, self.cell_height
            hover_surface = pygame.Surface(pygame.Rect(surface_region).size, pygame.SRCALPHA)
            pygame.draw.rect(hover_surface, (*HOVER_COLOUR, 128), hover_surface.get_rect())
            screen.blit(hover_surface, surface_region)

    def draw_features(self, screen: pygame.Surface):
        if not ENABLE_PERFORMANCE_OPTIMIZATIONS:
            self.draw_rectangles(screen)
        self.draw_characters(screen)
        if not ENABLE_PERFORMANCE_OPTIMIZATIONS:
            self.draw_hover(screen)
            self.draw_lines(screen)


class Boxes:

    def __init__(self, box_list: List[Box]):
        self.boxes = box_list

    def __getitem__(self, name: str) -> Box | CharacterBox | ArtBox:
        for box in self.boxes:
            if box.name == name:
                return box

    def __setitem__(self, name: str, value: Box | CharacterBox | ArtBox):
        for i, box in enumerate(self.boxes):
            if box.name == name:
                self.boxes[i] = value

    def get_selected_character(self) -> str:
        return self["character"].get_selected_character()

    def draw_box_features(self, screen: pygame.Surface):
        for box in self.boxes:
            box.draw_features(screen)

    def check_box_intersect(self, screen: pygame.Surface, mouse_position: tuple, mouse_event: int):
        for box in self.boxes:
            if box.position_in_box(mouse_position):
                box.on_intersect(screen,
                                 box.convert_mouse_position_to_coordinates(mouse_position),
                                 mouse_event,
                                 self.get_selected_character()
                                 )

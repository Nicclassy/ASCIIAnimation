import json
from typing import Tuple

import pygame

from constants import *
from button import Button
from boxes import Boxes, ArtBox, CharacterBox


def name_save_file(extension: str):
    filename = SAVE_FILE_NAME
    count = 0
    while filename + "." + extension in os.listdir(SAVED_FILES_DIRECTORY):
        if count != 0:
            filename = filename[:-1]
        count += 1
        filename += str(count)
    return filename + "." + extension


def load_json_file(filename: str) -> Tuple[list, list]:
    file_data = open(os.path.join(SAVED_FILES_DIRECTORY, filename)).read().split("\n")
    if len(file_data) == 1:
        art_box_data, character_box_data = json.loads(file_data[0]), None
    else:
        art_box_json_data, character_box_json_data = file_data
        art_box_data, character_box_data = json.loads(art_box_json_data), json.loads(character_box_json_data)
    return art_box_data, character_box_data


def format_character_list(character_list: list, add_newlines: bool = False) -> str:
    list_string = ""
    for row in character_list:
        list_string += "".join(char if char else NO_DATA for char in row) + "\n" * add_newlines
    return list_string


class SaveButton(Button):

    def __init__(self, colour: tuple, left: int, top: int, width: int, height: int, character: str = "",
                 font_size: int = 25):
        super().__init__(colour, left, top, width, height, character, font_size)

    @staticmethod
    def export(boxes: Boxes, json_file: bool = False, art_box_only: bool = False):
        if json_file:
            file = open(os.path.join(SAVED_FILES_DIRECTORY, name_save_file("json")), "w")
            export_boxes = [boxes["art"]]
            if not art_box_only:
                export_boxes.append(boxes["character"])
            string_data = ""
            for box in export_boxes:
                string_data += json.dumps(box.character_list) + "\n"
            file.write(string_data.rstrip("\n"))
            file.close()
        else:
            ascii_art = format_character_list(boxes["art"].character_list)
            file = open(os.path.join(SAVED_FILES_DIRECTORY, name_save_file("txt")), "w")
            file.write(ascii_art)
            if not art_box_only:
                characters = format_character_list(boxes["character"].character_list)
                file.write(characters)
            file.close()


class ClearButton(Button):

    def __init__(self, colour: tuple, left: int, top: int, width: int, height: int, character: str = "",
                 font_size: int = 25):
        super().__init__(colour, left, top, width, height, character, font_size)

    @staticmethod
    def clear_data(art_box: ArtBox, character_box: CharacterBox):
        art_box.character_list = [[NO_DATA] * art_box.list_width for _ in range(art_box.list_height)]
        character_box.character_list = [[NO_DATA] * character_box.list_width for _ in range(character_box.list_height)]
        character_box.selected_position = (0, 0)
        character_box.coordinate_generator.position = 0


class LoadButton(Button):

    def __init__(self, colour: tuple, left: int, top: int, width: int, height: int, character: str = "",
                 font_size: int = 25):
        super().__init__(colour, left, top, width, height, character, font_size)

    @staticmethod
    def load_last_file(boxes: Boxes) -> str | None:
        number_index = len(SAVE_FILE_NAME) + 1
        file_number_groupings = [
            (int(filename[number_index]) if filename[number_index].isdigit() else 0, filename)
            for filename in os.listdir(SAVED_FILES_DIRECTORY)
            if filename.endswith("json")
        ]
        file_number_groupings.sort(reverse=True)
        if last_created_file := file_number_groupings[:1]:
            chosen_filename = last_created_file[0][1]
            return LoadButton.load_file(chosen_filename, boxes)

    @staticmethod
    def load_file(filename: str, boxes: Boxes) -> str | None:
        if filename:
            art_box_data, character_box_data = load_json_file(filename)
            old_art_box, old_character_box = boxes["art"], boxes["character"]
            boxes["art"] = ArtBox(old_art_box.name, old_art_box.left_side_margin, old_art_box.right_side_margin,
                                  old_art_box.upper_margin, old_art_box.lower_margin, len(art_box_data or old_art_box),
                                  len((art_box_data or old_art_box)[0]), old_art_box.display_width,
                                  old_art_box.display_height,
                                  old_art_box.line_color, character_list=art_box_data)
            boxes["character"] = CharacterBox(old_character_box.name, old_character_box.left_side_margin,
                                              old_character_box.right_side_margin,
                                              old_character_box.upper_margin, old_character_box.lower_margin,
                                              len(character_box_data or old_character_box),
                                              len((character_box_data or old_character_box)[0]),
                                              old_character_box.display_width,
                                              old_character_box.display_height,
                                              old_character_box.line_color, character_list=character_box_data)

            return filename


class FPSCount(Button):

    def __init__(self, left: int, top: int, width: int, height: int, font_size: int):
        super().__init__((), left, top, width, height, font_size=font_size)

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, BACKGROUND_COLOUR, self.rect)

    def draw_frames(self, screen: pygame.Surface, frames: float):
        font = pygame.font.Font(pygame.font.get_default_font(), self.font_size)
        text_surface = font.render(str(int(frames)), True, TEXT_COLOUR)
        text_rect = text_surface.get_rect()
        text_rect.center = self.rect.left + self.rect.width // 2, self.rect.top + self.rect.height // 2
        screen.blit(text_surface, text_rect)

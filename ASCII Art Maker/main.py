from typing import Optional

import pygame

from button import Button
from constants import *
from keymods import shift_key, alt_key, shift_alt_key
from boxes import ArtBox, CharacterBox, Boxes
from interfacebuttons import SaveButton, ClearButton, LoadButton, FPSCount

os.chdir(os.path.dirname(__file__))

pygame.init()
pygame.display.set_caption('ASCII Art Maker', 'ASCIIAM')
pygame.display.set_icon(pygame.image.load("icon.png"))
clock = pygame.time.Clock()

pygame.event.set_allowed([pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.QUIT, pygame.WINDOWRESIZED])

FULLSCREEN = (pygame.display.Info().current_w, pygame.display.Info().current_h)

ART_BOX_HEIGHT = 10
ART_BOX_WIDTH = 30
CHARACTER_BOX_WIDTH = 5
CHARACTER_BOX_HEIGHT = 2


def main(display_width: int, display_height: int, character_box: Optional[CharacterBox] = None,
         art_box: Optional[ArtBox] = None, add_on_highlight: bool = True):
    display = pygame.display.set_mode((display_width, display_height),
                                      pygame.RESIZABLE | pygame.SCALED | pygame.DOUBLEBUF,
                                      32, vsync=1)
    UPPER_SPACING = 10
    SPACING = 50
    DIMENSION = 40

    SAVE_BUTTON_COLOUR = (213, 43, 43)
    CLEAR_BUTTON_COLOUR = (160, 96, 96)
    QUIT_BUTTON_COLOUR = (181, 75, 75)
    LOAD_PREVIOUS_BUTTON_COLOUR = (202, 54, 54)
    LOAD_SELECTED_BUTTON_COLOUR = (223, 33, 33)

    save_button = SaveButton(SAVE_BUTTON_COLOUR, UPPER_SPACING, UPPER_SPACING, DIMENSION, DIMENSION, character="S")
    clear_button = ClearButton(
        CLEAR_BUTTON_COLOUR, UPPER_SPACING, UPPER_SPACING + SPACING, DIMENSION, DIMENSION, character="C"
    )
    quit_button = Button(
        QUIT_BUTTON_COLOUR, UPPER_SPACING, UPPER_SPACING + SPACING * 2, DIMENSION, DIMENSION, character="Q"
    )
    load_previous_button = LoadButton(
        LOAD_PREVIOUS_BUTTON_COLOUR, UPPER_SPACING, UPPER_SPACING + SPACING * 3, DIMENSION, DIMENSION, character="P"
    )
    load_selected_button = LoadButton(
        LOAD_SELECTED_BUTTON_COLOUR, UPPER_SPACING, UPPER_SPACING + SPACING * 4, DIMENSION, DIMENSION, character="L"
    )
    frame_count = FPSCount(
        UPPER_SPACING, display_height - UPPER_SPACING * 4, DIMENSION, DIMENSION, 25
    )

    if character_box is None:
        character_box = CharacterBox("character", 70, 70, 10, display_height // 5 * 4, CHARACTER_BOX_HEIGHT,
                                     CHARACTER_BOX_WIDTH, display_width, display_height, CHARACTER_BOX_COLOUR)
    else:
        character_box = CharacterBox("character", 70, 70, 10, display_height // 5 * 4, character_box.list_height,
                                     character_box.list_width, display_width, display_height, CHARACTER_BOX_COLOUR,
                                     character_list=character_box.character_list)

    if art_box is None:
        art_box = ArtBox("art", 70, 70, display_height // 4, display_height // 20, ART_BOX_HEIGHT, ART_BOX_WIDTH,
                         display_width, display_height, ART_BOX_COLOUR)
    else:
        art_box = ArtBox("art", 70, 70, display_height // 4, display_height // 20,
                         art_box.list_height, art_box.list_width, display_width, display_height, ART_BOX_COLOUR,
                         character_list=art_box.character_list)
    boxes = Boxes([
        character_box,
        art_box,
    ])

    boxes["character"].add_character("│")

    if ENABLE_PERFORMANCE_OPTIMIZATIONS:
        display.fill(BACKGROUND_COLOUR)
        boxes["art"].draw_rectangles(display)
        boxes["art"].draw_lines(display)

    while 1:
        character_box = boxes["character"]
        art_box = boxes["art"]
        for event in pygame.event.get():
            match event.type:
                case pygame.QUIT:
                    pygame.quit()
                    quit()
                case pygame.KEYDOWN:
                    match event.key:
                        case pygame.K_LEFT:
                            character_box.move_highlight_left()
                        case pygame.K_RIGHT:
                            character_box.move_highlight_right()
                        case pygame.K_DOWN:
                            character_box.move_highlight_down()
                        case pygame.K_UP:
                            character_box.move_highlight_up()
                        case _:
                            # Special commands
                            mods = pygame.key.get_mods()
                            if event.key == pygame.K_q and mods & pygame.KMOD_META:
                                quit()
                            elif event.key == pygame.K_p and mods & pygame.KMOD_META:
                                for row in art_box.character_list:
                                    print("".join(character if character != NO_DATA else " " for character in row))
                            elif event.key == pygame.K_m and mods & pygame.KMOD_META:
                                add_on_highlight = not add_on_highlight
                            elif event.key == pygame.K_r and mods & pygame.KMOD_META:
                                art_box.fill_with_character(character_box.get_selected_character(), fill="row")
                            elif event.key == pygame.K_c and mods & pygame.KMOD_META:
                                art_box.fill_with_character(character_box.get_selected_character(), fill="column")
                            elif 0 < event.key <= 1114112:
                                character = chr(event.key)
                                if mods & pygame.KMOD_ALT and mods & pygame.KMOD_SHIFT:
                                    key = shift_alt_key(character)
                                elif mods & pygame.KMOD_ALT:
                                    key = alt_key(character)
                                elif mods & pygame.KMOD_SHIFT:
                                    key = shift_key(character)
                                else:
                                    key = character
                                if ord(key) in PERMITTED_CHARACTER_UNICODES:
                                    character_box.add_character(key, add_on_highlight=add_on_highlight)
                case pygame.MOUSEBUTTONDOWN:
                    boxes.check_box_intersect(display, pygame.mouse.get_pos(), event.button)
                    if save_button.clicked():
                        SaveButton.export(boxes, json_file=JSON_FILE, art_box_only=ART_BOX_ONLY)
                        print("Saved current data.")
                    elif clear_button.clicked():
                        ClearButton.clear_data(art_box, character_box)
                        print("Reset all characters.")
                    elif quit_button.clicked():
                        print("Qutting program.")
                        quit()
                    elif load_previous_button.clicked():
                        if (loaded_file := LoadButton.load_last_file(boxes)) is not None:
                            print(f"Loaded data from the last file exported named {loaded_file!r}.")
                        else:
                            print("No existing file to load.")
                    elif load_selected_button.clicked():
                        filename = open("load_file.txt").read().rstrip("\n")
                        if (loaded_file := LoadButton.load_file(filename, boxes)) is not None:
                            print(f"Loaded data from the selected file named {loaded_file!r}.")
                        else:
                            print("No existing file to load.")
                case pygame.WINDOWRESIZED:
                    main(display.get_width(), display.get_height(), character_box,
                         art_box, add_on_highlight=add_on_highlight)
        if not ENABLE_PERFORMANCE_OPTIMIZATIONS:
            display.fill(BACKGROUND_COLOUR)
        boxes.draw_box_features(display)
        Button.draw_all_buttons(display)
        frame_count.draw_frames(display, clock.get_fps())
        pygame.display.update((character_box.left_side_margin, character_box.upper_margin,
                               art_box.list_display_width,
                               art_box.list_display_height + character_box.list_display_height +
                               character_box.upper_margin))
        clock.tick(60)


main(DISPLAY_WIDTH, DISPLAY_HEIGHT, add_on_highlight=ADD_ON_HIGHLIGHT)

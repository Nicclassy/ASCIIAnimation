import pygame

from constants import TEXT_COLOUR


class Button:

    _instances = []

    def __new__(cls, *args, **kwargs):
        self = object.__new__(cls)
        cls._instances.append(self)
        return self

    def __init__(self, colour: tuple, left: int, top: int, width: int, height: int, character: str = "",
                 font_size: int = 25):
        self.rect = pygame.rect.Rect(left, top, width, height)
        self.colour = colour
        self.character = character
        self.font_size = font_size

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, self.colour, self.rect)
        font = pygame.font.Font(pygame.font.get_default_font(), self.font_size)
        text_surface = font.render(self.character, True, TEXT_COLOUR)
        text_rect = text_surface.get_rect()
        text_rect.center = self.rect.left + self.rect.width // 2, self.rect.top + self.rect.height // 2
        screen.blit(text_surface, text_rect)

    def clicked(self) -> bool:
        pos = pygame.mouse.get_pos()
        pressed = pygame.mouse.get_pressed(3)

        if self.rect.collidepoint(pos):
            if pressed[0] == 1:
                return True
        return False

    @classmethod
    def draw_all_buttons(cls, screen: pygame.Surface):
        for button in cls._instances:
            button.draw(screen)

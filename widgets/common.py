#!/usr/bin/python3
import pygame
import time


class Widget:
    def __init__(self, x: int, y: int):
        self.rect = pygame.Rect(x, y, 1, 1)

    def draw(self, target: pygame.Surface):
        target.fill(pygame.Color('white'), self.rect)

    def inform(self, e: pygame.event.EventType):
        pass

    def moused(self) -> bool:
        return self.rect.collidepoint(*pygame.mouse.get_pos())


class Button(Widget):
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.border_thickness = 2

    def draw(self, target: pygame.Surface):
        pygame.draw.rect(target, pygame.Color('white' if not self.moused() else 'red'), self.rect,
                         self.border_thickness)

    def inform(self, e: pygame.event.EventType):
        super().inform(e)
        if e.type == pygame.MOUSEBUTTONDOWN:
            self.action()

    def action(self):
        pass


class TextBox(Widget):
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.font = pygame.font.SysFont('BuiltIn', 32)
        self.color = pygame.Color('white')
        self.text = ''
        self.text_surface = pygame.Surface((0, 0))
        self.dirty = True
        self.border_thickness = 2
        self.cursor = 0

    def refresh_text(self):
        self.text_surface = self.font.render(self.text, True, self.color)
        self.dirty = False

    def draw(self, target: pygame.Surface):
        if self.dirty:
            self.refresh_text()
        pygame.draw.rect(target, self.color, self.rect, self.border_thickness)
        if self.moused() and int(time.time() * 2) % 2 == 0:
            x_pos = self.font.size(self.text[:self.cursor])[0]
            if self.cursor > 0:
                x_pos -= 2
            pygame.draw.line(target, self.color, (x_pos, self.rect.y), (x_pos, self.rect.y + self.rect.height), 2)
        target.blit(self.text_surface, self.rect)

    def inform(self, e: pygame.event.EventType):
        if e.type == pygame.KEYDOWN and self.moused():
            pl = pygame
            # Taken from https://github.com/Nearoo/pygame-text-input/blob/master/pygame_textinput.py#L63,
            # with attribution, with some minor tweaks.
            # COPYPASTA STARTS HERE.
            if e.key == pl.K_BACKSPACE:  # FIXME: Delete at beginning of line?
                self.text = self.text[:max(self.cursor - 1, 0)] + \
                            self.text[self.cursor:]

                # Subtract one from cursor_pos, but do not go below zero:
                self.cursor = max(self.cursor - 1, 0)
            elif e.key == pl.K_DELETE:
                self.text = self.text[:self.cursor] + self.text[self.cursor + 1:]

            elif e.key == pl.K_RETURN:
                return True

            elif e.key == pl.K_RIGHT:
                # Add one to cursor_pos, but do not exceed len(input_string)
                self.cursor = min(self.cursor + 1, len(self.text))

            elif e.key == pl.K_LEFT:
                # Subtract one from cursor_pos, but do not go below zero:
                self.cursor = max(self.cursor - 1, 0)

            elif e.key == pl.K_END:
                self.cursor = len(self.text)

            elif e.key == pl.K_HOME:
                self.cursor = 0

            else:
                # If no special key is pressed, add unicode of key to input_string
                self.text = self.text[:self.cursor] + e.unicode + self.text[self.cursor:]
            self.cursor += len(e.unicode)  # Some are empty, e.g. K_UP
            # COPYPASTA ENDS HERE.


class Label(Widget):
    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if key == 'text':
            self.dirty = True

    def __init__(self, x: int, y: int, text: str):
        super().__init__(x, y)
        self.text = text
        self.dirty = True
        self.text_surface = pygame.Surface((1, 1))
        self.font = pygame.font.SysFont('BuiltIn', 32)
        self.color = pygame.Color('white')

    def refresh_text(self):
        self.text_surface = self.font.render(self.text, True, self.color)
        self.dirty = False

    def draw(self, target: pygame.Surface):
        if self.dirty:
            self.refresh_text()
        target.blit(self.text_surface, self.rect)

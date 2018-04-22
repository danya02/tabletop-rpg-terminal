#!/usr/bin/python3
import pygame

import widgets.common


class ButtonWithText(widgets.common.Button):
    def __setattr__(self, key, value):
        super().__setattr__(key, value)
        if key == 'text':
            self.dirty = True

    def __init__(self, rect: pygame.Rect, target: callable, text: str):
        super().__init__(rect, target)
        self.text = text
        self.dirty = True
        self.text_surface = pygame.Surface((1, 1))
        self.font = pygame.font.SysFont('BuiltIn', self.rect.height)

    def redraw_text(self):
        self.text_surface = self.font.render(self.text, True, pygame.Color('white'))

    def draw(self, target: pygame.Surface):
        super().draw(target)
        if self.dirty:
            self.redraw_text()
        rect = self.text_surface.get_rect()
        rect.center = self.rect.center
        target.blit(self.text_surface, rect)

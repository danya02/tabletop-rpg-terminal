#!/usr/bin/python3
import threading
import pygame
import widgets


class MasterWindow:
    def __init__(self):
        pygame.init()
        self.surface = pygame.Surface((1, 1))
        self.display_clock = pygame.time.Clock()
        self.widgets = [widgets.common.Label(0, 0, 'Coming soon!')]
        self.running = True
        self.do_draw_loop = True
        self.init_screen()
        self.draw_loop_thread = threading.Thread(target=self.draw_loop, name='draw loop', daemon=False)
        self.draw_loop_thread.start()

    def init_screen(self):
        self.surface = pygame.display.set_mode((400, 50))

    def draw_loop(self):
        while self.running:
            if self.do_draw_loop:
                self.draw()

    def draw(self):
        self.display_clock.tick(30)
        self.surface.fill(pygame.Color('black'))
        for i in self.widgets:
            i.draw(self.surface)
        pygame.display.flip()

        for i in pygame.event.get():
            for j in self.widgets:
                j.inform(i)


if __name__ == '__main__':
    w = MasterWindow()

#!/usr/bin/python3
import socket
import threading
import pygame
import widgets


class MasterWindow:
    def __init__(self):
        pygame.init()
        self.surface = pygame.Surface((1, 1))
        self.display_clock = pygame.time.Clock()
        self.recv_clock = pygame.time.Clock()
        self.framerate = 30
        self.widgets = {'test_button': widgets.button.ButtonWithText((100, 0, 100, 50), lambda: print(self.widgets['test_textbox'].text), 'Test!'),
                        'test_textbox': widgets.common.TextBox((0, 0, 100, 20))}
        self.running = True
        self.do_draw_loop = True
        self.socket = socket.socket()
        self.connected = False
        self.packets = {}
        self.packet_num = 0
        self.init_screen()
        self.draw_loop_thread = threading.Thread(target=self.draw_loop, name='draw loop', daemon=False)
        self.draw_loop_thread.start()

    def init_screen(self):
        self.surface = pygame.display.set_mode((400, 50))

    def connect(self, ip: str, port: int):
        self.socket = socket.socket()
        self.socket.connect((ip, port))
        self.connected = True

    def draw_loop(self):
        while self.running:
            if self.do_draw_loop:
                self.draw()

    def draw(self):
        self.display_clock.tick(self.framerate)
        self.surface.fill(pygame.Color('black'))
        for i in self.widgets:
            self.widgets[i].draw(self.surface)
        pygame.display.flip()

        for i in pygame.event.get():
            for j in self.widgets:
                self.widgets[j].inform(i)

    def recv_packets(self):
        while self.running:
            if self.connected:
                self.recv_clock.tick(self.framerate)
                data = b''

                def eot(msg: bytes) -> bool:
                    try:
                        return msg[-1] == b'\n'[0]
                    except IndexError:
                        return False

                while not eot(data):
                    try:
                        newdata = self.socket.recv(1024)
                    except socket.timeout:
                        newdata = b''
                    data += newdata
                data = data.strip()
                self.parse_packet(data)

    def send(self, data: bytes):
        self.packet_num += 1
        self.socket.sendall(bytes(str(self.packet_num), 'utf8') + b':' + data)

    def parse_packet(self, data: bytes):
        id, response = data.split(b':')
        id = int(id)
        command = self.packets.pop(id)
        print(command, '->', response)


if __name__ == '__main__':
    w = MasterWindow()

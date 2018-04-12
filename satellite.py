#!/usr/bin/python3
import gzip

import pygame
import threading
import socket


class SatelliteDisplay:

    def __init__(self):
        self.recv_loop = True
        self.draw_loop = True
        self.event_loop = True
        self.update_now = True
        self.send_events = True
        self.socket = None
        self.conn = None
        self.addr = False
        self.connected = False
        self.recv_thread = None
        self.draw_thread = None
        self.display = pygame.Surface((1, 1))
        self.surface = pygame.Surface((1, 1))
        self.clock = pygame.time.Clock()
        self.framerate = 30
        self.init_socket()
        self.start_recv_loop()
        self.start_draw_loop()

    def init_screen(self):
        pygame.init()
        self.display = pygame.display.set_mode((320, 240))

    def init_socket(self):
        self.socket = socket.socket()
        self.socket.bind(('', 1234))
        self.socket.listen(1)
        self.conn, self.addr = self.socket.accept()
        self.conn.settimeout(5)

    def update_display(self):
        while self.draw_loop:
            while self.update_now:
                self.display.blit(self.surface, (0, 0))
            self.clock.tick(self.framerate)

    def get_events(self):
        while self.event_loop:
            while self.send_events:
                for i in pygame.event.get():
                    self.event(i)

    def start_recv_loop(self):
        self.recv_loop = False
        self.recv_thread = threading.Thread()
        self.recv_thread.name = 'socket parser loop'
        self.recv_thread.daemon = True
        self.recv_thread.run = self.recv_packets
        self.recv_loop = True
        self.recv_thread.start()

    def start_draw_loop(self):
        self.draw_loop = False
        self.draw_thread = threading.Thread()
        self.draw_thread.name = 'display updater loop'
        self.draw_thread.daemon = True
        self.draw_thread.run = self.update_display
        self.draw_loop = True
        self.draw_thread.start()

    def start_event_loop(self):
        self.event_loop = False
        self.event_thread = threading.Thread()
        self.event_thread.name = 'event sender loop'
        self.event_thread.daemon = True
        self.event_thread.run = self.get_events
        self.event_loop = True
        self.event_thread.start()

    def write_packet(self, packet: bytes):
        self.conn.writeall(packet)

    def ack(self, id: int):
        self.write_packet(bytes(str(id), 'utf8') + b':ACK')

    def nak(self, id: int):
        self.write_packet(bytes(str(id), 'utf8') + b':NAK')

    def event(self, event: pygame.event.EventType):
        self.write_packet(b'EVENT:' + bytes(str(event.type), 'utf8') + b':' + bytes(str(event.dict), 'utf8'))

    def parse_packet(self, packet: bytes):
        data = None
        try:
            id, command, data = packet.split(b':', 2)
        except ValueError:
            id, command = packet.split(b':')
        id = int(id)
        try:
            if command == b'fullscreen':
                pygame.display.toggle_fullscreen()
            elif command == b'setframerate':
                self.framerate = int(data)
            elif command == b'resize':
                x, y = data.split(b'x')
                x = int(x)
                y = int(y)
                self.display = pygame.display.set_mode((x, y))
            elif command == b'img':
                x, y, encoding, compression, imagestr = data.split(b':', 4)
                x = int(x)
                y = int(y)
                encoding = encoding.decode()
                compression = compression.decode()
                if compression == 'gzip':
                    imagestr = gzip.decompress(imagestr)
                elif compression == 'none':
                    pass
                else:
                    raise ValueError('compression method `{}` not supported'.format(compression))
                self.surface = pygame.image.fromstring(imagestr, (x, y), encoding)
            self.ack(id)
        except:
            self.nak(id)

    def recv_packets(self):
        while self.recv_loop:
            while self.connected:
                data = b''
                newdata = None
                while not newdata == b'':
                    try:
                        newdata = self.conn.recv(1024)
                    except socket.timeout:
                        newdata = b''
                    data += newdata
                self.parse_packet(data)

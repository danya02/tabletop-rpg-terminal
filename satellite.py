#!/usr/bin/python3
import pygame
import threading
import socket


class SatelliteDisplay:

    def __init__(self):
        self.loop = True
        self.s = None
        self.conn = None
        self.addr = False
        self.connected = False
        self.thread = False
        self.display = pygame.Surface((1, 1))
        self.init_socket()
        self.start_recv_loop()

    def init_screen(self):
        pygame.init()
        self.display = pygame.display.set_mode((320, 240))

    def init_socket(self):
        self.s = socket.socket()
        self.s.bind(('', 1234))
        self.s.listen(1)
        self.conn, self.addr = self.s.accept()
        self.conn.settimeout(5)

    def start_recv_loop(self):
        self.loop = False
        self.thread = threading.Thread()
        self.thread.name = 'socket parser loop'
        self.thread.daemon = True
        self.thread.run = self.recv_packets
        self.loop = True
        self.thread.start()

    def write_packet(self, packet: bytes):
        self.conn.writeall(packet)

    def ack(self, id: int):
        self.write_packet(bytes(str(id), 'utf8') + b':ACK')

    def nak(self, id: int):
        self.write_packet(bytes(str(id), 'utf8') + b':NAK')

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
            elif command == b'resize':
                x, y = data.split(b'x')
                x = int(x)
                y = int(y)
                self.display = pygame.display.set_mode((x, y))
            self.ack(id)
        except:
            self.nak(id)

    def recv_packets(self):
        while self.loop:
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

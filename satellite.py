#!/usr/bin/python3
import pygame
import socket

global s


class SatelliteDisplay:

    def __init__(self):
        self.loop = True
        self.s = None
        self.conn = None
        self.addr = False
        self.connected = False
        self.init_socket()

    def init_socket(self):
        self.s = socket.socket()
        self.s.bind(('', 1234))
        self.s.listen(1)
        self.conn, self.addr = self.s.accept()
        self.conn.settimeout(5)

    def parse_packet(self, packet: bytes):
        pass

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

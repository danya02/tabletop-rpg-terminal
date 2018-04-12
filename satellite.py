#!/usr/bin/python3
import pygame
import threading
import socket

global s


class SatelliteDisplay:

    def __init__(self):
        self.loop = True
        self.s = None
        self.conn = None
        self.addr = False
        self.connected = False
        self.thread = False
        self.init_socket()
        self.start_recv_loop()

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

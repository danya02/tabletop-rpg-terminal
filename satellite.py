#!/usr/bin/python3
import base64
import gzip
import math
import random
import time
import pygame
import threading
import socket
import traceback


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
        self.recv_clock = pygame.time.Clock()
        self.framerate = 30
        self.port = 1237
        self.init_socket()
        self.init_screen()
        self.start_recv_loop()
        self.wait_for_connection()

    def init_screen(self):
        pygame.init()
        self.display = pygame.display.set_mode((320, 240))

    def init_socket(self):
        self.socket = socket.socket()
        try:
            self.socket.bind(('', self.port))
        except socket.error:
            self.port = random.randint(1024, 65535)
            self.init_socket()
        self.socket.listen(1)

    @staticmethod
    def get_my_ips():  # taken from https://stackoverflow.com/a/1267524/5936187
        return [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] or [
            [(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in
             [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]

    def wait_for_connection(self):
        self.display = pygame.display.set_mode((320, 240))
        self.surface = pygame.Surface((320, 240))

        def draw_plug(center: (int, int), width: int, height: int, pin_len: int, cable_len: int):
            c = pygame.Color('white')
            r = pygame.Rect(0, 0, width, height)
            r.center = center
            pygame.draw.line(self.surface, c, r.center, (r.centerx - r.w // 2 - cable_len, r.centery), 10)
            y1 = r.centery + r.h // 4
            y2 = r.centery - r.h // 4
            pygame.draw.line(self.surface, c, (r.centerx, y1), (r.centerx + r.w // 2 + pin_len, y1), 5)
            pygame.draw.line(self.surface, c, (r.centerx, y2), (r.centerx + r.w // 2 + pin_len, y2), 5)
            self.surface.fill(c, r)

        def draw_socket(center: (int, int), width: int, height: int, cable_len: int):
            c = pygame.Color('white')
            r = pygame.Rect(0, 0, width, height)
            r.center = center
            pygame.draw.line(self.surface, c, r.center, (r.centerx + r.w // 2 + cable_len, r.centery), 10)
            self.surface.fill(c, r)

        x1 = 100
        x2 = 240
        f = pygame.font.SysFont('BuiltIn', 32)
        t_waiting = f.render('Waiting for connection...', True, pygame.Color('white'))
        t_ips = f.render('; '.join(['{}:{}'.format(i, self.port) for i in self.get_my_ips()]), True,
                         pygame.Color('white'))

        while not self.connected:
            self.surface.fill(pygame.Color('black'))
            x1 = int(100 + math.sin(time.time()) * 32)
            x2 = int(240 - math.sin(time.time()) * 32)
            draw_plug((x1, 120), 50, 100, 25, 50)
            draw_socket((x2, 120), 50, 100, 50)
            self.surface.blit(t_waiting, (0, 0))
            self.surface.blit(t_ips, (0, 200))
            self.socket.settimeout(0.01)
            try:
                self.conn, self.addr = self.socket.accept()
                self.conn.settimeout(0.001)
                self.connected = True
            except socket.timeout:
                pass
            self.flip()
        t_connected = f.render('Connected!', True, pygame.Color('white'))
        t_conn_ip = f.render(str(self.conn.getpeername()), True, pygame.Color('white'))
        self.surface.fill(pygame.Color('black'))
        draw_plug((138, 120), 50, 100, 25, 50)
        draw_socket((192, 120), 50, 100, 50)
        self.surface.blit(t_connected, (0, 0))
        self.surface.blit(t_conn_ip, (0, 200))
        self.flip()

    def flip(self):
        if self.update_now:
            self.display.blit(self.surface, (0, 0))
            pygame.display.flip()
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
        self.recv_thread.daemon = False
        self.recv_thread.run = self.recv_packets
        self.recv_loop = True
        self.recv_thread.start()

    def start_event_loop(self):
        self.event_loop = False
        self.event_thread = threading.Thread()
        self.event_thread.name = 'event sender loop'
        self.event_thread.daemon = True
        self.event_thread.run = self.get_events
        self.event_loop = True
        self.event_thread.start()

    def write_packet(self, packet: bytes):
        self.conn.sendall(packet + b'\n')

    def ack(self, id: int, extra: str = None):
        if extra is None:
            self.write_packet(bytes(str(id), 'utf8') + b':ACK')
        else:
            self.write_packet(bytes(str(id), 'utf8') + b':ACK:' + bytes(str(extra), 'utf8'))

    def nak(self, id: int, reason: str = None):
        if reason is None:
            self.write_packet(bytes(str(id), 'utf8') + b':NAK')
        else:
            self.write_packet(bytes(str(id), 'utf8') + b':NAK:' + bytes(reason, 'utf8'))

    def event(self, event: pygame.event.EventType):
        self.write_packet(b'EVENT:' + bytes(str(event.type), 'utf8') + b':' + bytes(str(event.dict), 'utf8'))

    def parse_packet(self, packet: bytes):
        data = None
        try:
            id, command, data = packet.split(b':', 2)
        except ValueError:
            try:
                id, command = packet.split(b':')
            except ValueError:
                return None
        id = int(id)
        retval = None
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
                elif compression=='base64':
                    imagestr = base64.b64decode(imagestr)
                elif compression=='base32':
                    imagestr = base64.b32decode(imagestr)
                elif compression=='base85':
                    imagestr = base64.a85decode(imagestr)
                elif compression=='base16':
                    imagestr = base64.b16decode(imagestr)
                elif compression == 'none':
                    pass
                else:
                    raise ValueError('compression method `{}` not supported'.format(compression))
                self.surface = pygame.image.fromstring(imagestr, (x, y), encoding)
            elif command == b'exec':
                code = data.decode()
                exec(code)
            elif command == b'eval':
                code = data.decode()
                retval = eval(code)
            elif command == b'ping':
                pass
            else:
                raise ValueError('command {} not supported'.format(command))
            self.ack(id, retval)
        except:
            exc = traceback.format_exc().split('\n')[-2]
            self.nak(id, exc)

    def recv_packets(self):
        while self.recv_loop:
            while self.connected:
                self.recv_clock.tick(self.framerate)
                data = b''

                def eot(msg: bytes) -> bool:
                    try:
                        return msg[-1] == b'\n'[0]
                    except IndexError:
                        return False

                while not eot(data):
                    try:
                        newdata = self.conn.recv(1024)
                    except socket.timeout:
                        newdata = b''
                    data += newdata
                data = data.strip()
                self.parse_packet(data)


if __name__ == '__main__':
    s = SatelliteDisplay()

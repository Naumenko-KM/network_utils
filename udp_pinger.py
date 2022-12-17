#!/usr/bin/env python3

from argparse import ArgumentParser
import random
import string
import socket
import time

class Pinger:
    NUM_PROBES = 10
    def __init__(self, dst_host, dst_port, my_host, my_port, min_probe_port, max_probe_port, payload, knock_period, my_name='unnamed'):
        self.my_name = my_name

        self.dst_host = dst_host
        self.dst_port = dst_port

        self.min_probe_port = min_probe_port
        self.max_probe_port = max_probe_port

        self.probe_port = None if dst_port else 1024

        self.payload_size = payload
        self.knock_period = knock_period

        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setblocking(False)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((my_host, my_port))

    def send_recv_pings(self):
        t0 = time.time()

        peer_knocked = False
        last_ping = 0
        last_knock = 0

        k = 0
        pk = 0
        while True:
            iter_time = time.time()
            if iter_time - last_ping >= 0.1:
                if self.dst_port is not None:
                    ping_time = time.time()
                    payload = ''.join(random.choices(string.ascii_uppercase + string.digits, k=self.payload_size))
                    msg = f"PING {pk} {ping_time:0.5f} from {self.my_name} PAYLOAD {payload}"
                    print(f'Sending "{msg[:100]}" to port {self.dst_port}')
                    self.s.sendto(msg.encode('utf8'), (self.dst_host, self.dst_port))
                    last_ping = ping_time
                    pk += 1

            if not peer_knocked and iter_time - last_knock >= self.knock_period:
                msg = f"KNOCK {k} from {self.my_name}"
                self.s.sendto(msg.encode('utf8'), (self.dst_host, self.probe_port))
                self.probe_port += 1
                if self.probe_port > self.max_probe_port:
                    self.probe_port = self.min_probe_port
                print(f'Sent probe msg to port {self.probe_port}')
                last_knock = iter_time

            try:
                ret, sender = self.s.recvfrom(65000)
                print(f'Got from {sender}', ret[:100])
                ret = ret.decode('utf8').split()

                if ret[0] == 'KNOCK':
                    if self.dst_port is None:
                        if sender[0] == self.dst_host:
                            print('Got knock!')
                            self.dst_port = sender[1]
                        else:
                            print('Got spurious message')
                elif ret[0] == 'PING':
                    peer_knocked = True
                    if self.dst_port:
                        msg = f"PONG {ret[1]} {ret[2]} from {self.my_name} {ret[5]} {ret[6]}"
                        print(f'Replying "{msg[:100]}" to port {self.dst_port}')
                        self.s.sendto(msg.encode('utf8'), (self.dst_host, self.dst_port))
                elif ret[0] == 'PONG':
                    dt = time.time() - float(ret[2])
                    print(f'Received PONG {ret[1]} dt {dt:.6f}')
                else:
                    print('Strange msg', ret)

            except BlockingIOError:
                pass

            k += 1


def main():
    parser = ArgumentParser()
    parser.add_argument("--my_port", type=int, help='my port')
    parser.add_argument("--my_host", default='0.0.0.0')
    parser.add_argument("--name", default='def_pinger')
    parser.add_argument("--dst_host")
    parser.add_argument("--dst_port", type=int)
    parser.add_argument("--min_probe_port", type=int, default=1024)
    parser.add_argument("--max_probe_port", type=int, default=4000)
    parser.add_argument("--payload", type=int, default=1)
    parser.add_argument('--knock_period', type=float, default=0.01)

    args = parser.parse_args()

    pinger = Pinger(args.dst_host, args.dst_port, my_host=args.my_host, my_port=args.my_port, my_name=args.name,
                    min_probe_port = args.min_probe_port, max_probe_port=args.max_probe_port,
                    payload=args.payload, knock_period=args.knock_period)
    pinger.probe_port = args.min_probe_port
    pinger.send_recv_pings()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3

from argparse import ArgumentParser
import socket
import time

class Pinger:
    NUM_PROBES = 10
    def __init__(self, dst_host, dst_port, my_host, my_port, min_probe_port, max_probe_port, my_name='unnamed'):
        self.my_name = my_name

        self.dst_host = dst_host
        self.dst_port = dst_port

        self.min_probe_port = min_probe_port
        self.max_probe_port = max_probe_port

        self.probe_port = None if dst_port else 1024

        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setblocking(False)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((my_host, my_port))

    def send_recv_pings(self):
        for k in range(100000):
            msg = f"PING {k} from {self.my_name}"
            if self.dst_port:
                print(f'Sending {msg} to port {self.dst_port}')
                self.s.sendto(msg.encode('utf8'), (self.dst_host, self.dst_port))
            else:
                p0 = self.probe_port
                for i in range(self.NUM_PROBES):
                    self.s.sendto(msg.encode('utf8'), (self.dst_host, self.probe_port))
                    self.probe_port += 1
                    if self.probe_port > self.max_probe_port:
                        self.probe_port = self.min_probe_port
                p1 = self.probe_port

                print(f'Sent burst of {self.NUM_PROBES} msgs to ports {p0}-{p1}')


            try:
                ret, sender = self.s.recvfrom(1024)
                print(f'Got from {sender}', ret)
                if sender[0] == self.dst_host and self.dst_port is None:
                    self.dst_port = sender[1]

            except BlockingIOError:
                pass

            time.sleep(0.01 if self.dst_port is None else 1)


def main():
    parser = ArgumentParser()
    parser.add_argument("--my_port", type=int, help='my port')
    parser.add_argument("--my_host", default='0.0.0.0')
    parser.add_argument("--name", default='def_pinger')
    parser.add_argument("--dst_host")
    parser.add_argument("--dst_port", type=int)
    parser.add_argument("--min_probe_port", type=int, default=1024)
    parser.add_argument("--max_probe_port", type=int, default=4000)

    args = parser.parse_args()

    pinger = Pinger(args.dst_host, args.dst_port, my_host=args.my_host, my_port=args.my_port, my_name=args.name, min_probe_port = args.min_probe_port, max_probe_port=args.max_probe_port)
    pinger.probe_port = args.min_probe_port
    pinger.send_recv_pings()


if __name__ == '__main__':
    main()

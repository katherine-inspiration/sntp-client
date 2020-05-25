import socket
import datetime
import time
import struct
import random


def get_fraction(number, precision):
    return int((number - int(number)) * 2 ** precision)


class NTPData:
    _FORMAT = "!B B B b 11I"

    def __init__(self, transmit_timestamp=0.0, mode=3, version_number=4):
        self.leap_indicator = 0
        self.version_number = version_number
        self.mode = mode
        self.transmit = transmit_timestamp
        self.stratum = 0
        self.poll = 0
        self.precision = 0
        self.root_delay = 0
        self.root_dispersion = 0
        self.reference_id = 0
        self.reference = 0
        self.originate = 0
        self.receive = 0

    def pack(self):
        return struct.pack(NTPData._FORMAT,
                           (self.leap_indicator << 6) + (self.version_number << 3) + self.mode,
                           self.stratum,
                           self.poll,
                           self.precision,
                           (int(self.root_delay) << 16) + get_fraction(self.root_delay, 16),
                           (int(self.root_dispersion) << 16) + get_fraction(self.root_dispersion, 16),
                           self.reference_id,
                           int(self.reference),
                           get_fraction(self.reference, 32),
                           int(self.originate),
                           get_fraction(self.originate, 32),
                           int(self.receive),
                           get_fraction(self.receive, 32),
                           int(self.transmit),
                           get_fraction(self.transmit, 32))

    def unpack(self, data: bytes):
        unpacked_data = struct.unpack(NTPData._FORMAT, data)
        self.leap_indicator = unpacked_data[0] >> 6
        self.version_number = (unpacked_data[0] >> 3) & 0b111
        self.mode = unpacked_data[0] & 0b111
        self.stratum = unpacked_data[1]
        self.poll = unpacked_data[2]
        self.precision = unpacked_data[3]
        self.root_delay = (unpacked_data[4] >> 16) + (unpacked_data[4] & 0xFFFF) / 2 ** 16
        self.root_dispersion = (unpacked_data[5] >> 16) + (unpacked_data[5] & 0xFFFF) / 2 ** 16
        self.reference_id = str((unpacked_data[6] >> 24) & 0xFF) + str((unpacked_data[6] >> 16) & 0xFF) + str(
            (unpacked_data[6] >> 8) & 0xFF) + str(unpacked_data[6] & 0xFF)
        self.reference = unpacked_data[7] + unpacked_data[8] / 2 ** 32
        self.originate = unpacked_data[9] + unpacked_data[10] / 2 ** 32
        self.receive = unpacked_data[11] + unpacked_data[12] / 2 ** 32
        self.transmit = unpacked_data[13] + unpacked_data[14] / 2 ** 32
        return self

    def to_display(self):
        return ("Leap indicator: {0.leap_indicator}\n" + "Version number: {0.version_number}\n" + "Mode: {0.mode}\n" +
                "Stratum: {0.stratum}\n" + "Poll: {0.poll}\n" + "Precision: {0.precision}\n" + "Root delay: {0.root_delay}\n" +
                "Root dispersion: {0.root_dispersion}\n" + "Ref id: {0.ref_id}\n" + "Reference: {0.reference}\n" +
                "Originate: {0.originate}\n" + "Receive: {0.receive}\n" + "Transmit: {0.transmit}").format(self)


TIME_FORMAT_DIFF = (datetime.date(1970, 1, 1) - datetime.date(1900, 1, 1)).days * 24 * 3600
WAITING_TIME = 5
servers = ["ntp.psn.ru", "clock.psu.edu", "Time2.Stupi.SE"]
port = 123


def get_server(servers):
    return servers[random.randint(0, len(servers) - 1)]


def get_time(server):
    print("NTP-сервер", server)
    data = NTPData(time.time() + TIME_FORMAT_DIFF)
    answer = NTPData()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(WAITING_TIME)
    response = ""
    try:
        sock.sendto(data.pack(), (server, port))
        response = sock.recv(48)
    except Exception:
        print("Проблемы с доступом к NTP-серверу. Попробуйте ввести другой адрес.")

    arrive_time = time.time() + TIME_FORMAT_DIFF
    answer.unpack(response)
    print("""\
Время на NTP-сервере : {stratum_time},\n\
Время на вашем компьютере : {arrive_time}\n""".format(stratum_time=datetime.datetime.fromtimestamp(answer.transmit +
                                                                                                   (
                                                                                                               arrive_time - answer.originate -
                                                                                                               (
                                                                                                                           answer.transmit - answer.receive)) / 2 - TIME_FORMAT_DIFF),
                                                      arrive_time=datetime.datetime.fromtimestamp(
                                                          arrive_time - TIME_FORMAT_DIFF)))


while True:
    print("Введите NTP-сервер или просто нажмите Enter")
    server_input = input()
    if server_input.strip() != "":
        get_time(server_input.strip())
    else:
        get_time(get_server(servers))

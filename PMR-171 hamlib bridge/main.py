# PMR-171 Rigctl Bridge
# Copyright (C) 2025 Raid10Without1
#
# 本程序是自由软件，你可以依据 GNU 通用公共许可证（GPLv3）条款重新发布和修改它。
# 本程序是基于“现状”提供的，没有任何担保，包括适销性或特定用途的适用性。
# 详情请参阅 <https://www.gnu.org/licenses/gpl-3.0.html>
import socket
import serial
import struct
import threading
import crcmod
import serial.tools.list_ports
import sys
import signal

class PMR171Bridge:
    def __init__(self, serial_port, baudrate=115200):
        self.ser = serial.Serial(serial_port, baudrate=baudrate, timeout=1)
        self.lock = threading.Lock()
        self.crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)

    # 模式映射表（class attribute）
    MODE_MAP = {
        0: 'USB',
        1: 'LSB',
        2: 'CWR',
        3: 'CWL',
        4: 'AM',
        5: 'WFM',
        6: 'NFM',
        7: 'DIGI',
        8: 'PKT'
    }
    # 获取模式名 → ID
    @classmethod
    def mode_name_to_id(cls, name: str) -> int:
        name = name.upper()
        for id_, s in cls.MODE_MAP.items():
            if s == name:
                return id_
        return 0  # fallback to USB

    # 获取模式ID → 名称
    @classmethod
    def mode_id_to_name(cls, mode_id: int) -> str:
        return cls.MODE_MAP.get(mode_id, 'USB')

    def build_packet(self, cmd_type, data: bytes):
        pkt = b'\xA5\xA5\xA5\xA5'
        body = bytes([cmd_type]) + data
        pktlen = len(body)
        pkt += bytes([pktlen]) + body
        crc = self.crc16(pkt[4:])
        pkt += struct.pack('>H', crc)
        return pkt

    def send_packet(self, pkt):
        with self.lock:
            self.ser.write(pkt)

    def set_freq(self, freq_hz: int):
        b = struct.pack('>II', freq_hz, freq_hz)
        pkt = self.build_packet(0x09, b)
        self.send_packet(pkt)

    def set_mode(self, mode_id_or_str):
        if isinstance(mode_id_or_str, str):
            mode_id = self.mode_name_to_id(mode_id_or_str)
        else:
            mode_id = mode_id_or_str
        b = struct.pack('BB', mode_id, mode_id)
        pkt = self.build_packet(0x0A, b)
        self.send_packet(pkt)
    def get_mode(self) -> str:
        pkt = self.build_packet(0x0B, b'')
        with self.lock:
            self.ser.write(pkt)
            response = self.ser.read(64)

        if not response.startswith(b'\xA5\xA5\xA5\xA5'):
            return 'USB 2400'

        try:
            payload = response[6:]
            mode_id = payload[0]  # VFOA 模式
            mode_str = self.mode_id_to_name(mode_id)
            return f'{mode_str} 2400'
        except Exception:
            return 'USB 2400'

    def set_ptt(self, ptt_on: bool):
        b = bytes([0x00 if ptt_on else 0x01])
        pkt = self.build_packet(0x07, b)
        self.send_packet(pkt)

def select_serial_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("未检测到任何串口设备。")
        sys.exit(1)
    print("检测到以下串口设备：")
    for i, port in enumerate(ports):
        print(f"{i + 1}: {port.device} - {port.description}")
    while True:
        try:
            index = int(input("请选择串口编号：")) - 1
            if 0 <= index < len(ports):
                return ports[index].device
            else:
                print("无效编号，请重新输入。")
        except ValueError:
            print("请输入数字编号。")

def rigctl_server(bridge: PMR171Bridge, host='127.0.0.1', port=4532):
    def handle(client_socket):
        with client_socket:
            while True:
                try:
                    cmd = client_socket.recv(128).decode().strip()
                    if not cmd:
                        break
                    if cmd == 'q':
                        break
                    elif cmd.startswith('F'):
                        freq = int(cmd[1:].strip())
                        bridge.set_freq(freq)
                        client_socket.send(b'RPRT 0\n')
                    elif cmd == 'f':
                        client_socket.send(b'14074000\n')
                    elif cmd.startswith('M'):
                        _, mode, width = cmd.split()
                        mode_map = {
                            'USB': 0, 'LSB': 1, 'CWR': 2, 'CWL': 3,
                            'AM': 4, 'WFM': 5, 'NFM': 6, 'DIGI': 7, 'PKT': 8
                        }
                        bridge.set_mode(mode_map.get(mode.upper(), 0))
                        client_socket.send(b'RPRT 0\n')
                    elif cmd == 'v':
                        client_socket.send(b'PMR-171\n')
                    elif cmd == 'V':
                        client_socket.send(b'1.0.0\n')
                    elif cmd == 'm':
                        mode = bridge.get_mode()
                        client_socket.send(f"{mode}\n".encode())
                    elif cmd.startswith('T'):
                        state = cmd[1:].strip()
                        bridge.set_ptt(state == '1')
                        client_socket.send(b'RPRT 0\n')
                    elif cmd == 't':
                        client_socket.send(b'0\n')
                    else:
                        client_socket.send(b'RPRT -1\n')
                except Exception as e:
                    print(f"命令处理异常: {e}")
                    break

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"rigctl 中转服务启动于 {host}:{port}")
        while True:
            try:
                conn, _ = s.accept()
                threading.Thread(target=handle, args=(conn,), daemon=True).start()
            except Exception as e:
                print(f"Socket异常: {e}")
def get_freq(self) -> int:
        """请求当前频率并返回 VFOA 频率（单位 Hz）"""
        pkt = self.build_packet(0x0B, b'')  # 状态同步命令
        with self.lock:
            self.ser.write(pkt)
            response = self.ser.read(64)  # 根据实际长度调整，64字节足够
        if not response.startswith(b'\xA5\xA5\xA5\xA5'):
            return 0  # 解析失败

        # 提取频率数据：VFOA 频率在偏移位置 10（包长+命令+VFOA mode+VFOB mode）
        try:
            # 找到数据起始点
            payload_start = 4 + 1 + 1 + 1 + 1  # 包头+包长+命令+2字节模式
            vfoa_bytes = response[payload_start:payload_start+4]
            freq = struct.unpack('>I', vfoa_bytes)[0]
            return freq
        except Exception:
            return 0


        """读取当前模式，返回 rigctl 格式的字符串，如 'USB 2400'"""
        pkt = self.build_packet(0x0B, b'')
        with self.lock:
            self.ser.write(pkt)
            response = self.ser.read(64)

        if not response.startswith(b'\xA5\xA5\xA5\xA5'):
            return 'USB 2400'  # fallback

        try:
            # 模式字节通常在第 6~7 字节（包头4 + 长度1 + 命令1 + 模式2）
            payload = response[6:]
            mode_id = payload[0]  # VFOA 模式
            mode_map = {
                0: 'USB',
                1: 'LSB',
                2: 'CWR',
                3: 'CWL',
                4: 'AM',
                5: 'WFM',
                6: 'NFM',
                7: 'DIGI',
                8: 'PKT'
            }
            mode_str = mode_map.get(mode_id, 'USB')
            return f'{mode_str} 2400'
        except Exception:
            return 'USB 2400'

def main():
    def signal_handler(sig, frame):
        print("\n程序已退出。")
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    serial_port = select_serial_port()
    bridge = PMR171Bridge(serial_port)
    rigctl_server(bridge)



if __name__ == '__main__':
    main()

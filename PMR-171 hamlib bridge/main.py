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

    def set_mode(self, mode_id: int):
        b = struct.pack('BB', mode_id, mode_id)
        pkt = self.build_packet(0x0A, b)
        self.send_packet(pkt)

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

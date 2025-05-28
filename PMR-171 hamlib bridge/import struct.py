import struct
import crcmod

# test_main.py

from PMR-171 hamlib bridge.main import build_pmr_packet, pmr_set_freq, pmr_set_mode, pmr_set_ptt

def test_build_pmr_packet_basic():
    # cmd_type 0x01, data b'\x02\x03'
    pkt = build_pmr_packet(0x01, b'\x02\x03')
    assert pkt[:4] == b'\xA5\xA5\xA5\xA5'
    assert pkt[5] == 0x01
    assert pkt[6:8] == b'\x02\x03'
    # 长度字段
    assert pkt[4] == 3
    # CRC 校验
    crc = pkt[-2:]
    body = pkt[4:-2]
    # 重新计算 CRC
    crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
    assert crc == struct.pack('>H', crc16(body))

def test_pmr_set_freq():
    freq = 12345678
    pkt = pmr_set_freq(freq)
    # 命令类型
    assert pkt[5] == 0x09
    # 频率字段
    vfoa = struct.unpack('>I', pkt[6:10])[0]
    vfob = struct.unpack('>I', pkt[10:14])[0]
    assert vfoa == freq
    assert vfob == freq

def test_pmr_set_mode():
    mode_id = 3
    pkt = pmr_set_mode(mode_id)
    assert pkt[5] == 0x0A
    assert pkt[6] == mode_id
    assert pkt[7] == mode_id

def test_pmr_set_ptt_on():
    pkt = pmr_set_ptt(True)
    assert pkt[5] == 0x07
    assert pkt[6] == 0x00

def test_pmr_set_ptt_off():
    pkt = pmr_set_ptt(False)
    assert pkt[5] == 0x07
    assert pkt[6] == 0x01
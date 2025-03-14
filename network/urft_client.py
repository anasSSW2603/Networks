import socket
import sys
import struct
import hashlib
import os

CHUNK_SIZE = 1024
ACK_TIMEOUT = 3.0
MAX_RETRIES = 3

def udp_client(file_path, server_ip, server_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(ACK_TIMEOUT)

    filename = os.path.basename(file_path)
    sock.sendto(filename.encode(), (server_ip, server_port))

    with open(file_path, 'rb') as f:
        seq = 0
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            checksum = hashlib.md5(chunk).digest()

            # ส่งข้อมูล 1024 ไบต์ + 4 ไบต์สำหรับ Sequence + 32 ไบต์สำหรับ checksum
            packet = struct.pack('!I32s1024s', seq, checksum, chunk.ljust(1024, b'\x00'))

            retries = 0
            while retries < MAX_RETRIES:
                sock.sendto(packet, (server_ip, server_port))
                try:
                    ack, _ = sock.recvfrom(4)
                    ack_seq = struct.unpack('!I', ack)[0]
                    if ack_seq == seq:
                        seq += 1
                        break
                except socket.timeout:
                    retries += 1
                    print(f"Retry {retries} for packet {seq}")

    print("File sent successfully.")
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python udp_client.py <file_path> <server_ip> <server_port>")
        sys.exit(1)

    udp_client(sys.argv[1], sys.argv[2], int(sys.argv[3]))

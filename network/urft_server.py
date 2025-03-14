import socket
import sys
import struct
import hashlib

CHUNK_SIZE = 1024
ACK_TIMEOUT = 3.0
MAX_RETRIES = 3

def udp_server(server_ip, server_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((server_ip, server_port))
    print(f"Server listening on {server_ip}:{server_port}")
    
    while True:
        # รับชื่อไฟล์จากไคลเอนต์
        data, addr = sock.recvfrom(256)
        filename = data.decode().strip()
        print(f"Receiving file: {filename}")

        with open(filename, 'wb') as f:
            expected_seq = 0
            while True:
                try:
                    # รับข้อมูลขนาดใหม่ (เช่น 2048 ไบต์)
                    data, addr = sock.recvfrom(2048)  # ขยายขนาด buffer

                    # ตรวจสอบขนาดข้อมูลที่รับมาว่าตรงกับที่คาดไว้
                    if len(data) != 2048:
                        print(f"Warning: Received data size is {len(data)}, expected 2048 bytes.")
                        continue  # ข้ามหากขนาดข้อมูลไม่ตรงกับที่คาด

                    seq, checksum, payload = struct.unpack('!I32s1024s', data[:1060])  # แยกข้อมูลตามขนาดที่เพิ่ม
                    recv_checksum = hashlib.md5(payload).digest()

                    # ตรวจสอบว่า sequence และ checksum ตรงกันหรือไม่
                    if seq == expected_seq and recv_checksum == checksum:
                        f.write(payload.rstrip(b'\x00'))  # เขียนข้อมูลลงในไฟล์
                        expected_seq += 1
                        sock.sendto(struct.pack('!I', seq), addr)  # ส่ง ACK กลับไปยัง client
                    else:
                        # ส่ง ACK สำหรับ sequence ที่คาดหวัง
                        sock.sendto(struct.pack('!I', expected_seq - 1), addr)

                except socket.timeout:
                    print("Timeout reached, stopping file reception.")
                    break  # ออกจากลูปหากหมดเวลา

        print(f"File '{filename}' received successfully.")
    
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python udp_server.py <server_ip> <server_port>")
        sys.exit(1)

    udp_server(sys.argv[1], int(sys.argv[2]))

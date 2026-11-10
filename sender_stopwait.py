#sender_stopwait.py

import socket
import time
import os

def main():
    host = "127.0.0.1"
    port = 12000

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)

    server_address = (host, port)

    # File to send
    filename = input("Enter the name of the file to send: ")

    if not os.path.exists(filename):
        print("File not found.")
        sock.close()
        return

    # Read file contents
    file_handle = open(filename, "rb")
    file_data = file_handle.read()
    file_handle.close()

    # Divide file into packets
    packet_size = 1024
    packets = []

    for i in range(0, len(file_data), packet_size):
        packets.append(file_data[i:i + packet_size])

    print("File:", filename)
    print("File size:", len(file_data), "bytes")
    print("Number of packets:", len(packets))

    timeout = 1.0
    retransmissions = 0

    # 1. Notify receiver that file transfer is starting
    start_packet = b"START:0:"

    while True:
        sock.sendto(start_packet, server_address)
        print("Sent START packet.")

        try:
            ack, addr = sock.recvfrom(1024)

            if ack == b"ACK:0":
                print("Received START acknowledgment.")
                break

        except socket.timeout:
            retransmissions += 1
            print("START timeout. Retransmitting...")

    # 2. Send file data using Stop-and-Wait
    seq_num = 0

    for packet_data in packets:

        packet = f"DATA:{seq_num}:".encode("utf-8") + packet_data

        acknowledged = False

        while not acknowledged:

            # Send one packet
            sock.sendto(packet, server_address)
            print("Sent DATA packet", seq_num)

            try:
                ack, addr = sock.recvfrom(1024)

                ack_parts = ack.decode("utf-8").split(":")

                if len(ack_parts) == 2:
                    ack_type = ack_parts[0]
                    ack_num = int(ack_parts[1])

                    if ack_type == "ACK" and ack_num == seq_num:
                        print("Received ACK", ack_num)
                        acknowledged = True

            except socket.timeout:
                retransmissions += 1
                print("Timeout. Retransmitting packet", seq_num)

        # Alternate between sequence numbers 0 and 1
        seq_num = 1 - seq_num

    # 3. Notify receiver that file transfer is complete
    end_packet = f"END:{seq_num}:".encode("utf-8")

    while True:
        sock.sendto(end_packet, server_address)
        print("Sent END packet.")

        try:
            ack, addr = sock.recvfrom(1024)

            if ack == f"ACK:{seq_num}".encode("utf-8"):
                print("Received final ACK.")
                break

        except socket.timeout:
            retransmissions += 1
            print("END timeout. Retransmitting...")

    print("\nFile transfer completed successfully.")
    print("Total retransmissions:", retransmissions)

    sock.close()


if __name__ == "__main__":
    main()

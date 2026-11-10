# receiver_stopwait.py
# CP372 Assignment 2 - Stop-and-Wait Receiver

import socket
import os

def main():
    host = "127.0.0.1"
    port = 12000
    
    # create UDP socket and bind it
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"Stop-and-Wait receiver up and listening on port {port}...")

    expected_seq = 0
    file_handle = None
    output_filename = "received_file.txt"

    while True:
        packet, addr = sock.recvfrom(4096)
        if not packet:
            break
            
        # parse packet format: TYPE:SEQ:PAYLOAD
        try:
            parts = packet.split(b":", 2)
            pkt_type = parts[0].decode('utf-8')
            seq_num = int(parts[1].decode('utf-8'))
            payload = parts[2] if len(parts) > 2 else b""
        except Exception as e:
            print("Error parsing incoming packet:", e)
            continue

        # 1. Handle file transfer start notification
        if pkt_type == "START":
            file_handle = open(output_filename, "wb")
            expected_seq = 0
            print(f"Incoming file transfer started. Saving as '{output_filename}'")
            
            # send ACK back
            ack_msg = f"ACK:{seq_num}".encode('utf-8')
            sock.sendto(ack_msg, addr)

        # 2. Handle incoming data packets
        elif pkt_type == "DATA":
            if seq_num == expected_seq:
                if file_handle:
                    file_handle.write(payload)
                
                # send acknowledgement for the received packet
                ack_msg = f"ACK:{seq_num}".encode('utf-8')
                sock.sendto(ack_msg, addr)
                print(f"Received correct data packet {seq_num}, ACK sent.")
                
                # flip expected sequence bit (0 -> 1 or 1 -> 0)
                expected_seq = 1 - expected_seq
            else:
                # duplicate or out of order packet - resend last valid ACK
                last_ack_seq = 1 - expected_seq
                ack_msg = f"ACK:{last_ack_seq}".encode('utf-8')
                sock.sendto(ack_msg, addr)
                print(f"Ignored out-of-order/duplicate packet {seq_num}. Resending ACK {last_ack_seq}.")

        # 3. Handle completion notice
        elif pkt_type == "END":
            if file_handle:
                file_handle.close()
            print("File transfer completed successfully. File saved and closed.")
            
            # send final ACK
            ack_msg = f"ACK:{seq_num}".encode('utf-8')
            sock.sendto(ack_msg, addr)
            break

    sock.close()

if __name__ == "__main__":
    main()
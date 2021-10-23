import config
import threading
import time
import udt
import util


# Selective Repeat reliable transport protocol.
class SelectiveRepeat:

    NO_PREV_ACK_MSG = "Don't have previous ACK to send, will wait for server to timeout."

    # "msg_handler" is used to deliver messages to application layer
    def __init__(self, local_port, remote_port, msg_handler):
        util.log("Starting up `Selective Repeat` protocol ... ")
        self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
        self.msg_handler = msg_handler
        self.sender_base = 0
        self.next_sequence_number = 0
        self.timer_list = [self.set_timer(-1)] * config.WINDOW_SIZE
        self.ack_list = [False] * config.WINDOW_SIZE
        self.sender_buffer = [b''] * config.WINDOW_SIZE
        self.receiver_last_ack = b''
        self.is_receiver = True
        self.receiver_base = 0
        self.rcv_list = [False] * config.WINDOW_SIZE
        self.rcv_buffer = [b''] * config.WINDOW_SIZE
        self.sender_lock = threading.Lock()

    def set_timer(self, seq_num):
        return threading.Timer((config.TIMEOUT_MSEC / 1000.0), self._timeout,
                               {seq_num: seq_num})

    # "send" is called by application. Return true on success, false otherwise.
    def send(self, msg):
        self.is_receiver = False
        if self.next_sequence_number < (self.sender_base + config.WINDOW_SIZE):
            self._send_helper(msg)
            return True
        else:
            util.log("Window is full. App data rejected.")
            time.sleep(1)
            return False

    # Helper fn for thread to send the next packet
    def _send_helper(self, msg):
        self.sender_lock.acquire()
        packet = util.make_packet(msg, config.MSG_TYPE_DATA,
                                  self.next_sequence_number)
        packet_data = util.extract_data(packet)
        util.log("Sending data: " + util.pkt_to_string(packet_data))
        self.network_layer.send(packet)
        if self.next_sequence_number < self.sender_base + config.WINDOW_SIZE:
            packet_offset_index = (self.next_sequence_number -
                                   self.sender_base) % config.WINDOW_SIZE
            print(packet_offset_index)
            self.sender_buffer[packet_offset_index] = packet
            self.ack_list[packet_offset_index] = False
            self.timer_list[packet_offset_index] = self.set_timer(
                self.next_sequence_number)
            self.timer_list[packet_offset_index].start()
            self.next_sequence_number += 1
        else:
            pass
        self.sender_lock.release()
        return

    # "handler" to be called by network layer when packet is ready.
    def handle_arrival_msg(self):
        msg = self.network_layer.recv()
        msg_data = util.extract_data(msg)

        if (msg_data.is_corrupt):
            return

        # If ACK message, assume its for sender
        if msg_data.msg_type == config.MSG_TYPE_ACK:
            self.sender_lock.acquire()
            packet_offset_index = (msg_data.seq_num -
                                   self.sender_base) % config.WINDOW_SIZE
            print(packet_offset_index)
            self.ack_list[packet_offset_index] = True
            print('sender cancel timer after receiving ack')

            util.log("Received ACK with seq #" + util.pkt_to_string(msg_data) +
                     ". Cancelling timer.")
            self.timer_list[packet_offset_index].cancel()
            self.timer_list[packet_offset_index] = self.set_timer(
                msg_data.seq_num)

            for timer in self.timer_list:
                print(timer.is_alive())

            # check if the packet right after sendbase is ack'd
            # if yes, move sendbase
            # update the arrays (timer_list, ack_list) accordingly
            # by removing first element, and add empty timer, and False ack
            try:
                while self.ack_list[0] == True:
                    self.sender_base += 1
                    util.log(f"Updated send base to {self.sender_base}")
                    self.ack_list = self.ack_list[1:] + [False]
                    self.timer_list = self.timer_list[1:] + [
                        self.set_timer(-1)
                    ]
                    self.sender_buffer = self.sender_buffer[1:] + [b'']
            except IndexError:
                pass

            self.sender_lock.release()

        # If DATA message, assume its for receiver
        else:
            assert msg_data.msg_type == config.MSG_TYPE_DATA
            util.log("Received DATA: " + util.pkt_to_string(msg_data))

            ack_pkt = util.make_packet(b'', config.MSG_TYPE_ACK,
                                       msg_data.seq_num)

            if msg_data.seq_num in range(
                    self.receiver_base,
                    self.receiver_base + config.WINDOW_SIZE):
                self.network_layer.send(ack_pkt)
                util.log("Sent ACK: " +
                         util.pkt_to_string(util.extract_data(ack_pkt)))
                packet_offset_index = (msg_data.seq_num -
                                       self.receiver_base) % config.WINDOW_SIZE
                self.rcv_list[packet_offset_index] = True

                if msg_data.seq_num != self.receiver_base:
                    # Append the payload
                    self.rcv_buffer[packet_offset_index] = msg_data.payload

                else:
                    # Append the payload
                    self.rcv_buffer[packet_offset_index] = msg_data.payload
                    while self.rcv_list[0] == True:
                        self.msg_handler(self.rcv_buffer[0])
                        self.receiver_base += 1
                        self.rcv_list = self.rcv_list[1:] + [False]
                        self.rcv_buffer = self.rcv_buffer[1:] + [b'']
                        util.log(
                            f"Updated receiver base to {self.receiver_base}")

            elif msg_data.seq_num < self.receiver_base:

                self.network_layer.send(ack_pkt)
                util.log("Packet outside receiver window")
                util.log("Sent ACK: " +
                         util.pkt_to_string(util.extract_data(ack_pkt)))

            else:
                return

        return

    # Cleanup resources.
    def shutdown(self):
        if not self.is_receiver: self._wait_for_last_ACK()
        for timer in self.timer_list:
            print(timer.is_alive())
            if timer.is_alive(): timer.cancel()
        util.log("Connection shutting down...")
        self.network_layer.shutdown()

    def _wait_for_last_ACK(self):
        while self.sender_base < self.next_sequence_number - 1:
            util.log("Waiting for last ACK from receiver with sequence # " +
                     str(int(self.next_sequence_number - 1)) + ".")
            time.sleep(1)

    def _timeout(self, seq_num):
        util.log(f"Timeout! Resending packet {seq_num}")
        self.sender_lock.acquire()
        packet_offset_index = (seq_num - self.sender_base) % config.WINDOW_SIZE
        self.timer_list[packet_offset_index].cancel()
        self.timer_list[packet_offset_index] = self.set_timer(seq_num)
        pkt = self.sender_buffer[packet_offset_index]
        self.network_layer.send(pkt)
        util.log("Resending packet: " +
                 util.pkt_to_string(util.extract_data(pkt)))
        self.timer_list[packet_offset_index].start()
        self.sender_lock.release()
        return
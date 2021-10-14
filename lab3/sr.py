import config
import threading
import time
import udt
import util


# Go-Back-N reliable transport protocol.
class SelectiveRepeat:

  NO_PREV_ACK_MSG = "Don't have previous ACK to send, will wait for server to timeout."

  # "msg_handler" is used to deliver messages to application layer
  def __init__(self, local_port, remote_port, msg_handler):
    util.log("Starting up `Selective Repeat` protocol ... ")
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.msg_handler = msg_handler
    self.sender_base = 0
    self.next_sequence_number = 0
    #set the time list for each packet

    self.timer = [self.set_timer(-1)]*config.WINDOW_SIZE
    self.sender_buffer = [b''] * config.WINDOW_SIZE
    self.ack_list = [False] * config.WINDOW_SIZE
    self.window = [b'']*config.WINDOW_SIZE
    self.is_receiver = True
    self.receiver_base = 0
    self.rcv = [False] * config.WINDOW_SIZE
    self.rcv_buffer = [b''] *config.WINDOW_SIZE
    self.sender_lock = threading.Lock()


  def set_timer(self, count):
    return threading.Timer((config.TIMEOUT_MSEC/1000.0), self._timeout, {count:count})


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
    packet = util.make_packet(msg, config.MSG_TYPE_DATA, self.next_sequence_number)
    packet_data = util.extract_data(packet)
    util.log("Sending data: " + util.pkt_to_string(packet_data))
    self.network_layer.send(packet) 
    #check if next seq number is in the sender window  
    if self.next_sequence_number < (self.sender_base + config.WINDOW_SIZE):

      count = (self.next_sequence_number - self.sender_base)% config.WINDOW_SIZE
      print(f"The value of the offset is {count}")
      #self.timer[count] = self.set_timer(count)
      
      #store inside the buffer for sender to remember that the packet was sent over
      self.sender_buffer[count] = packet
      self.ack_list[count] = False
      self.timer[count] = self.set_timer(self.next_sequence_number)
      self.timer[count].start()
      self.next_sequence_number += 1
    self.sender_lock.release()
    return


  # "handler" to be called by network layer when packet is ready.
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    msg_data = util.extract_data(msg)

    if(msg_data.is_corrupt):
      util.log("Packet received is corrupted. " + self.NO_PREV_ACK_MSG)
      return
        
    # If ACK message, assume its for sender
    if msg_data.msg_type == config.MSG_TYPE_ACK:
      self.sender_lock.acquire()
      count = (msg_data.seq_num - self.sender_base) % config.WINDOW_SIZE
      util.log("Received ACK with seq # matching the end of the window: "
                 + util.pkt_to_string(msg_data) + ". Cancelling timer.")

      #if self.timer[count].is_alive(): self.timer[count].cancel()
      
      self.ack_list[count] = True
      self.timer[count].cancel()
      self.timer[count] = self.set_timer(msg_data.seq_num)
      #if the sck is alr acked
      #shift right 
      while self.ack_list[0] == True:
        self.sender_base += 1
        util.log(f"Sender base is now {self.sender_base}")
        self.ack_list = self.ack_list[1:] + [False]
        self.timer = self.timer[1:] + [self.set_timer(-1)]
        self.sender_buffer = self.sender_buffer[1:] + [b'']
      self.sender_lock.release()

    # If DATA message, assume its for receiver
    else:
      assert msg_data.msg_type == config.MSG_TYPE_DATA
      util.log("Received DATA: " + util.pkt_to_string(msg_data))
      ack_pkt = util.make_packet(b'', config.MSG_TYPE_ACK, msg_data.seq_num)
      if msg_data.seq_num in range(self.receiver_base, self.receiver_base + config.WINDOW_SIZE):
        self.msg_handler(msg_data.payload)
        self.network_layer.send(ack_pkt)
        #self.receiver_last_ack = ack_pkt
        util.log("Sent ACK: " + util.pkt_to_string(util.extract_data(ack_pkt)))
        count = (msg_data.seq_num - self.receiver_base)% config.WINDOW_SIZE
        self.rcv[count] = True 
        self.rcv_buffer[count] = msg_data.payload
      
      #received alr 
        while self.rcv[0] == True:
          self.msg_handler(self.rcv_buffer[0])
          self.receiver_base += 1
          self.rcv = self.rcv[1:] + [False]
          self.rcv_buffer = self.rcv_buffer[1:] + [b'']
          util.log("updated the receiver base")
      #not received, please buffer
      elif msg_data.seq_num < self.receiver_base:
        self.network_layer.send(ack_pkt)
        util.log("packet is outside the receiver window")
        util.log("sent ACK Packet")
        util.log("Sent ACK: " + util.pkt_to_string(util.extract_data(ack_pkt)))



  # Cleanup resources.
  def shutdown(self):
    if not self.is_receiver: self._wait_for_last_ACK()
    for timer_pkt in self.timer:
      if timer_pkt.is_alive(): timer_pkt.cancel()
    util.log("Connection shutting down...")
    self.network_layer.shutdown()


  def _wait_for_last_ACK(self):
    while self.sender_base < self.next_sequence_number-1:
      util.log("Waiting for last ACK from receiver with sequence # "
               + str(int(self.next_sequence_number-1)) + ".")
      time.sleep(1)


  def _timeout(self, count):
    pkt_num = (count - self.sender_base)%config.WINDOW_SIZE
    util.log("Timeout! Resending packet with seq #s "
             + str(pkt_num) +".")
    self.sender_lock.acquire()
    if self.timer[pkt_num].is_alive(): self.timer[pkt_num].cancel()
    self.timer[pkt_num] = self.set_timer(count)

    pkt = self.sender_buffer[pkt_num]
    self.network_layer.send(pkt)
    util.log("Resending packet: " + util.pkt_to_string(util.extract_data(pkt)))
    self.timer[pkt_num].start()
    self.sender_lock.release()
    return

import time
from enum import Enum
from queue import Queue

SENDER_PACKET_AMOUNT = 10
SENDER_TIMER_SECONDS = 5


class PacketStatus(Enum):
    WAITING = 0
    SENT = 1
    ACKED = 2


class SenderPacket():
    def __init__(self, seqnum):
        self.seqnum = seqnum
        self.status = PacketStatus.WAITING 

    def set_status(self, status):
        self.status = status
    
    def get_status(self):
        return self.status

    def get_seqnum(self):
        return self.seqnum


class GBNSender:
    def __init__(self, n, id):
        self.n = n
        self.packet_amount = SENDER_PACKET_AMOUNT
        self.inbox_queue = Queue()
        self.base = 0
        self.packets = {i: SenderPacket(i) for i in range(self.packet_amount)}
        self.timer = Timer(SENDER_TIMER_SECONDS)
        self.next_seqnum = 0   # Next packet to send
        self.is_done = False
        self.timeout_duration = 5

        self.timer.restart()

    def done(self):
        """
            Return True if all the packets have been acknowledged

            Preconditions: 
            Postconditions: 

        """
        for packet in self.packets.values():
            if packet.get_status() != PacketStatus.ACKED:
                return False
        return True
    
    def get_window(self):
        seqnums = list(self.packets.keys())
        return seqnums[self.base:self.base + self.n]

    def get_packet(self, seqnum):
        return self.packets[seqnum]

    def get_next_seqnum(self):
        for seqnum in self.get_window():
            packet = self.get_packet(seqnum)
            if packet.get_status() == PacketStatus.ACKED:
                continue
            if packet.get_status() == PacketStatus.SENT: 
                continue
            elif packet.get_status() == PacketStatus.WAITING:
                return seqnum
        return None

    def send(self, seqnum):
        packet = self.packets[seqnum]
        # insert channel interface logic...
        print(f"Sending packet {self.next_seqnum}")

    def ACK(self, seqnum):
        """
          Cumulative Ack: every packet < seqnum is ACK'd.  
        """
        if seqnum < self.base:
            raise "Receiving a redundant or duplicate ACK"
            return

        packet = self.packets[seqnum]
        self.acknowledged.append(seqnum)
        self.base = seqnum + 1 

    def handle_timeout(self):
        print("Timeout!")
        self.resend_group()

    def resend_group(self, max_seqnum):
        print(f"Resending unacknowledged packets lower than {max_seqnum}")
        for seqnum in self.window:
            if seqnum <= max_seqnum:
               self.send(seqnum) 
    
    def print_debugs(self):
        print(f"Acks: {self.acknowledged}")
        print(f"Window: {self.window}")
        print(f"Expected: {self.expected_seqnum}")
        print(f"Next seq: {self.next_seqnum}")
        print(f"Remaining time: {self.timer.remaining_seconds}")

    def update(self):
        self.send(self.get_next_seqnum())
        remaining_time = self.timer.update()
        if remaining_time == 0:
            self.handle_timeout()


class Timer:
    def __init__(self, duration):
        self.duration = duration 
        self.remaining_seconds = None
        self.start_time = None   # Will be set to the current time when the timer starts

    def is_active(self):
        return self.remaining_seconds > 0

    def restart(self):
        self.active = True
        self.remaining_seconds = self.duration 
        self.start_time = time.time()

    def set_duration(self, seconds):
        self.duration = seconds

    def update(self):
        if not self.is_active():
            return
        now = time.time()
        passed_time = now - self.start_time
        self.remaining_seconds -= max(passed_time, 0)
        
        return self.remaining_seconds


class GBNReceiver:
    def __init__(self):
        self.ack_queue = Queue()
        self.received = []
        self.expected_seqnum = 0   # Oldest not-received packet
    
    def get_expected_seqnum(self):
        if len(self.received) == 0:
            return 0
        else:
            return self.received[-1] -1

    def on_receive(self, seqnum):
        if seqnum == self.expected_seqnum:
            self.received.append(seqnum)
        else:
            print(f"Packet {seqnum} was received out of order and discarded")
        latest_seqnum = self.received[-1]
        self.send_ack(latest_seqnum)

    def send_ack(self):
        seqnum = self.expected_seqnum - 1
        # insert channel interface logic ...

    def update(self):
        while not self.ack_queue.empty():
            seqnum = self.ack_queue.get()
            self.send_ack(seqnum)


class Channel:

    class ChannelItem:
        class ItemStatus(Enum):
            GOING = 0
            EXITED = 1
            KILLED = 2

        def __init__(self, seqnum, destination_id, type):
            self.seqnum = seqnum
            self.destination_id = destination_id
            self.timer = Timer()
            self.status = ItemStatus.GOING
        
        def exit(self):
            self.status = ItemStatus.EXITED

        def update(self):
            self.timer.update()

            if not self.timer.is_active():
                self.exit()

            return self.status

    def __init__(self, traversal_duration_sec):
        self.connectors = []
        self.traversal_duration = traversal_duration_sec
        self.items = []
    
    def update(self):
        self.update_items()
    def update_items(self):
        for item in self.items:
            status = item.update()
            if status == ItemStatus.EXITED:
                receiving_connector = self.getConnector(item.destination_id)
                receiving_connector.receive(item)
                self.items.remove(item)
            if status == ItemStatus.KILLED:   # Killed
                self.items.remove(item)

    def add_host(self, connector):
        self.connectors.append(connector)

    def handle_new_item(self, item):
        item.timer.restart(self.traversal_duration)
        self.items.append(item)

    def getConnector(self, id):
        for c in self.connectors:
            if c.id == id:
                return c
        return None


class ChannelInterface:
    def __init__(self, id, inbox_queue, channel):
        self.id = id
        self.channel = channel
        self.inbox_queue = inbox_queue

    def pushItem(self, item):
        self.channel.handle_new_item(item)

    def receive(self, item):
        self.inbox_queue.put(item.seqnum)


def run_simulation(sender, receiver, channel):
    print("Started running.\n")
    done = sender.is_done
    while not done:
        sender.update()
        receiver.update()
        channel.update_items()
        time.sleep(0.6)
        done = sender.is_done



if __name__ == "__main__":
    channel = Channel(traversal_duration_sec=1)
    sender = GBNSender(n=7, id=1)
    sender_connector = ChannelInterface(
            id=1,
            inbox_queue=sender.inbox_queue,
            channel=channel
    )
    receiver = GBNReceiver()
    receiver_connector = ChannelInterface(
            id=2,
            inbox_queue=receiver.ack_queue,
            channel=channel
    )
    channel.add_host(sender_connector)
    channel.add_host(receiver_connector)
    run_simulation(sender, receiver, channel)
    exit(0)

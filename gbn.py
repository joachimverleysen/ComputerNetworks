import time
from enum import Enum
from queue import Queue


class GBN:
    def __init__(self, id, n, packet_amount, channel):
        self.id = id
        self.n = n
        self.packet_amount = packet_amount
        self.channel = channel
        self.inbox_queue = Queue()
        self.receiver_id = None
        self.base = 0
        self.packet_list = [i+1 for i in range(packet_amount)]
        self.acknowledged = []
        self.sent_packets = []
        self.timer = Timer()
        self.window = self.packet_list[self.base:self.base+n]
        self.expected_seqnum = None   # First unacknowledged packet
        self.next_seqnum = 0   # Next packet to send
        self.isDone = False
        self.timeout_duration = 5

        self.timer.restart(self.timeout_duration)

    def done(self):
        if self.packet_list[-1] in self.acknowledged:
            return True
        return False

    def updateWindow(self):
        self.window = self.packet_list[self.base:self.base+self.n]
    def setReceiver(self, id):
        self.receiver_id = id

    def getNextSeqnum(self):
        for seqnum in self.window:
            if seqnum in self.acknowledged:
                continue
            if seqnum in self.sent_packets:
                continue
            return seqnum
        return None

    def pushToChannel(self, seqnum):
        channel_item = ChannelItem(seqnum, self.receiver_id, ChannelItemType(0))
        self.channel.handleNewItem(channel_item)

    def send(self):
        # Send the first unacknowledged packet
        if self.next_seqnum == None:
            print("Unable to send")
            return None
        self.sent_packets.append(self.next_seqnum)
        self.pushToChannel(self.next_seqnum)
        print(f"Sending packet {self.next_seqnum}")
        if self.next_seqnum == self.getExpectedSeqnum():
            self.expected_seqnum = self.next_seqnum
        return self.next_seqnum

    def acknowledge(self, seqnum):
        if seqnum in self.acknowledged:
            return
        self.acknowledged.append(seqnum)
        self.base += 1
        self.expected_seqnum += 1
        if seqnum == self.packet_amount:
            self.isDone = True
            print("Last ACK received")

    def handleReceiveACK(self, max_seqnum):
        print(f"Cumulative ACK  -  {max_seqnum}")
        for seqnum in self.window:
            if seqnum <= max_seqnum:
                self.acknowledge(seqnum)
        # Restart timer
        if self.expected_seqnum in self.acknowledged:
            self.timer.restart(self.timeout_duration)

    def getExpectedSeqnum(self):
        for seqnum in self.window:
            if seqnum not in self.acknowledged:
                return seqnum

    def handleTimeout(self):
        print("Timeout!")
        self.resendGroup()

    def resendGroup(self):
        if self.expected_seqnum == None:
            print("Unable to resend")
        print(f"Resending packets, starting at {self.expected_seqnum}")
        for seqnum in self.window:
            if seqnum >= self.expected_seqnum:
                self.sent_packets.append(seqnum)

    def handleInbox(self):
        while not self.inbox_queue.empty():
            new_seqnum = self.inbox_queue.get()
            self.handleReceiveACK(new_seqnum)

    def update(self):
        self.handleInbox()
        self.updateWindow()
        self.expected_seqnum = self.getExpectedSeqnum()
        self.next_seqnum = self.getNextSeqnum()
        self.send()
        self.isDone = self.done()
        remaining_time = self.timer.update()
        print(f"Acks: {self.acknowledged}")
        print(f"Window: {self.window}")
        print(f"Expected: {self.expected_seqnum}")
        print(f"Next seq: {self.next_seqnum}")
        print(f"Remaining time: {self.timer.remaining}")
        if remaining_time == 0:
            self.handleTimeout()
        # Update base
        # Window slides automatically base = self.expected_seqnum


class Timer:
    def __init__(self):
        self.remaining = None
        self.start_time = None
        self.active = False

    def hasStopped(self):
        return not self.active

    def restart(self, seconds):
        self.active = True
        self.remaining = seconds
        self.start_time = time.time()

    def update(self):
        if not self.active:
            return
        now = time.time()
        passed_time = now - self.start_time
        self.remaining -= passed_time
        if self.remaining <= 0:
            self.remaining = 0
            self.active = False
        return self.remaining


class Host:
    def __init__(self, id, channel):
        self.channel = channel
        self.ack_queue = Queue()
        self.received = []
        self.expected_seqnum = 0
        self.receiver_id = None

    def handleReceive(self, seqnum):
        if seqnum == self.expected_seqnum:
            self.received.append(seqnum)
        else:
            print(f"Packet {seqnum} was received out of order and discarded")
        latest_seqnum = self.received[-1]
        self.sendACK(latest_seqnum)

    def sendACK(self, seqnum):
        item = ChannelItem(seqnum, self.receiver_id, ChannelItemType(1))
        channel.handleNewItem(item)

    def setReceiver(self, id):
        self.receiver_id = id

    def update(self):
        while not self.ack_queue.empty():
            seqnum = self.ack_queue.get()
            self.sendACK(seqnum)


class ChannelItem:
    def __init__(self, seqnum, destination_id, type):
        self.seqnum = seqnum
        self.destination_id = destination_id
        self.type = type
        self.timer = Timer()
        self.status = ChannelItemStatus(0)

    def update(self):
        self.timer.update()
        if self.timer.hasStopped():
            self.status = ChannelItemStatus(1)
        return self.status


class ChannelItemStatus(Enum):
    GOING = 0
    EXITED = 1
    KILLED = 2


class ChannelItemType(Enum):
    PACKET = 0
    ACK = 1


class Channel:
    def __init__(self, traverse_duration_sec):
        self.connectors = []
        self.traverse_duration = traverse_duration_sec
        self.items = []

    def update(self):
        for item in self.items:
            status = item.update()
            if status == ChannelItemStatus.EXITED:
                receiving_connector = self.getConnector(item.destination_id)
                receiving_connector.receive(item)
                self.items.remove(item)
            if status == ChannelItemStatus.KILLED:   # Killed
                self.items.remove(item)

    def addHost(self, connector):
        self.connectors.append(connector)

    def handleNewItem(self, item):
        item.timer.restart(self.traverse_duration)
        self.items.append(item)

    def getConnector(self, id):
        for c in self.connectors:
            if c.host_id == id:
                return c
        return None


class ChannelConnectorType(Enum):
    HOST = 0
    CHANNEL = 1


class ChannelConnector:
    def __init__(self, host_id, host_inbox_queue, type: ChannelConnectorType, channel):
        self.host_id = host_id
        self.type = type
        self.channel = channel
        self.host_inbox_queue = host_inbox_queue

    def pushItem(self, item: ChannelItem):
        self.channel.handleNewItem(item)

    def receive(self, item):
        self.host_inbox_queue.put(item.seqnum)


def runSimulation(gbn, host, channel):
    print("Started running.\n")
    done = gbn.isDone
    while not done:
        gbn.update()
        host.update()
        channel.update()
        time.sleep(0.6)
        done = gbn.isDone



if __name__ == "__main__":
    channel = Channel(traverse_duration_sec=1)
    gbn = GBN(id=1, n=7, packet_amount=15, channel=channel)
    gbn_connector = ChannelConnector(
            host_id=1,
            host_inbox_queue=gbn.inbox_queue,
            type=ChannelConnectorType(0),
            channel=channel
    )
    host = Host(id=2, channel=channel)
    host_connector = ChannelConnector(
            host_id=2,
            host_inbox_queue=host.ack_queue,
            type=ChannelConnectorType(0),
            channel=channel
    )
    gbn.setReceiver(id=2)
    host.setReceiver(id=1)
    channel.addHost(gbn_connector)
    channel.addHost(host_connector)
    runSimulation(gbn, host, channel)
    exit(0)

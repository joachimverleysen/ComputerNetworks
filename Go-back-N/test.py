# Basic example of testing a module with the "unitest" library

import unittest
from queue import Queue
from gbn import GBNSender
from gbn import Channel
from gbn import ChannelInterface



class TestChannel(unittest.TestCase):
    def setUp(self):
        self.inbox_queue_1 = Queue() 
        self.inbox_queue_2 = Queue() 

        self.channel = Channel(traversal_duration_sec=1)

        self.connector_1 = ChannelInterface(
            id=1,
            inbox_queue=self.inbox_queue_1,
            channel=self.channel
        )

        self.connector_2 = ChannelInterface(
            id=2,
            inbox_queue=self.inbox_queue_2,
            channel=self.channel
        )

    def test_add_host(self):
        self.channel.add_host(self.connector_1)
        self.assertEqual(len(self.channel.get_connectors()), 1)
        self.channel.add_host(self.connector_2)
        self.assertEqual(len(self.channel.get_connectors()), 2)

if __name__ == "__main__":
    unittest.main()


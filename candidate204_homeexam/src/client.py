import socket
import struct
from datetime import datetime

class fileSender:
    '''
    Description:
    This class implements a file sender using UDP/DRTP protocol.

    Attributes:
    serverIP (str): The IP address of the server.
    serverPort (int): The port number of the server.
    filePath (str): The path to the file to be sent.
    windowSize (int): The size of the sliding window for packet transmission.
    window (dict): Dictionary to store packets in the sliding window.
    earliestUnackPacket (int): The sequence number of the earliest unacknowledged packet.
    nextSeq (int): The sequence number of the next packet to be sent.
    socket (socket.socket): The socket object for communication.
    packetTimeout (float): The timeout duration for packet retransmission.
    ackReceived (set): Set to store received acknowledgment packet sequence numbers.

    Methods:
    __init__: Initializes the fileSender object.
    start: Starts the file sending process.
    threeWayHandshake: Performs the three-way handshake protocol.
    timestamp: Returns the current timestamp.
    sendFile: Sends the file to the server.
    checkForTimeouts: Checks for packet timeouts and performs retransmissions.
    receiveAck: Receives acknowledgment packets from the server.
    resend: Resends packets in the window upon timeout.
    teardown: Initiates the teardown process by sending FIN packet.
    '''

    def __init__(client, serverIP, serverPort, filePath, windowSize=3):
        '''
        Description:
        Initializes the fileSender object with the parameters above.

        Arguments:
        serverIP (str): The IP address of the server.
        serverPort (int): The port number of the server.
        filePath (str): The path to the file to be sent.
        windowSize (int, optional): The size of the sliding window for packet transmission. Defaults to 3.

        Use of other input and output parameters in the function:
        Initializes the socket and sets a timeout. Sets up the initial state of the object, including the file path, sliding window size, etc.

        Returns None
        '''
        client.serverIP = serverIP
        client.serverPort = serverPort
        client.filePath = filePath
        client.windowSize = windowSize
        client.window = {}
        client.earliestUnackPacket = 1
        client.nextSeq = 1
        client.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client.packetTimeout = 0.5
        client.socket.settimeout(client.packetTimeout)  # 500ms timeout
        client.ackReceived = set()

    def start(client):
        '''
        Description:
        Starts the file sending process.

        Use of other input and output parameters in the function:
        Performs the three-way handshake with the server.
        Sends the file using the sendFile method.
        Initiates the teardown process after sending the file.

        Returns None
        '''
        try:
            client.threeWayHandshake()
            client.sendFile()
            client.teardown()
        finally:
            client.socket.close()

    def threeWayHandshake(client):
        '''
        Description:
        Performs the three-way handshake protocol for connection establishment.

        Use of other input and output parameters in the function:
        Sends a SYN packet to the server, waits for a SYN-ACK response, and then sends an ACK packet to establish the connection.

        Returns None

        Raises:
        Exception: If the SYN-ACK packet is not received
        '''
        # Send SYN Packet
        synPacket = struct.pack('!HHH', 0, 0, 8)
        client.socket.sendto(synPacket, (client.serverIP, client.serverPort))
        print("SYN packet is sent")

        # Receive SYN-ACK Packet
        synAckPacket, _ = client.socket.recvfrom(1000)
        _, _, synAckFlags = struct.unpack('!HHH', synAckPacket[:6])
        if synAckFlags & 12:
            print("SYN-ACK packet is received")
        else:
            raise Exception("Connection not established")

        # Send ACK Packet to establish connection between client and server
        ackPacket = struct.pack('!HHH', 0, 0, 4) 
        client.socket.sendto(ackPacket, (client.serverIP, client.serverPort))
        print("ACK packet is sent")
        print("Connection established")

    def timestamp(client) -> str:
        '''
        Description:
        Returns the current timestamp in a specific format.

        Use of other input and output parameters in the function:
        Uses the datetime module to get the current time and format it.

        Returns:
        str: The timestamp in 'HH:MM:SS.sss' format.
        '''
        return datetime.now().strftime('%H:%M:%S.%f')[:-3]

    def sendFile(client):
        '''
        Description:
        Sends the file to the server.

        Use of other input and output parameters in the function:
        Reads the file in chunks and sends them as packets. Manages the sliding window and handles acknowledgments.

        Returns None
        '''
        with open(client.filePath, 'rb') as file:
            while True:
                # Fill the window with packets
                while client.windowSize > len(client.window):
                    data = file.read(994)
                    if not data:
                        break
                    packet = struct.pack('!HHH994s', client.nextSeq, 0, 0, data)
                    client.window[client.nextSeq] = {'packet': packet, 'sent_time': datetime.now()}
                    client.socket.sendto(packet, (client.serverIP, client.serverPort))
                    print(f"{client.timestamp()} -- packet {client.nextSeq} is sent, sliding window = {list(client.window.keys())}")
                    client.nextSeq += 1

                client.receiveAck()
                
                client.checkForTimeouts()

                if not client.window:
                    break

    def checkForTimeouts(client):
        '''
        Description:
        Checks for packet timeouts and performs retransmission.

        Use of other input and output parameters in the function:
        Iterates through the packets in the sliding window and checks if any have timed out. If so, triggers a retransmission.

        Returns None 
        '''
        for _, info in list(client.window.items()):
            if (datetime.now() - info['sent_time']).total_seconds() > client.packetTimeout:
                print(f"{client.timestamp()} -- RTO Occured")
                client.resend()

    def receiveAck(client):
        '''
        Description:
        Receives acknowledgment packets from the server.

        Use of other input and output parameters in the function:
        Waits for acknowledgment packets from the server. Updates the sliding window and retransmits packets if necessary.

        Returns None
        '''
        try:
            ackPacket, _ = client.socket.recvfrom(1000)
            _, ackSeq, ackFlags = struct.unpack('!HHH', ackPacket[:6])
            if ackFlags & 4:  
                if ackSeq not in client.ackReceived:  # Check if ackSeq is not already received
                    print(f"{client.timestamp()} -- ack for packet {ackSeq} is received")
                    client.ackReceived.add(ackSeq)  # Add ackSeq to the set of received acknowledgments
                    if ackSeq in client.window:
                        del client.window[ackSeq]
                    client.earliestUnackPacket = ackSeq + 1
            
        except socket.timeout:
            # Resend all packets in the window if timeout
            client.resend()


    def resend(client):
        '''
        Description:
        Resends packets in the window upon timeout.

        Use of other input and output parameters in the function:
        Retransmits all packets currently in the sliding window.

        Returns None
        '''
        for seq, info in client.window.items():
            client.socket.sendto(info['packet'], (client.serverIP, client.serverPort))
            print(f"{client.timestamp()} -- retransmitting packet {seq}")

    def teardown(client):
        '''
        Description:
        Initiates the teardown process by sending FIN packet.

        Use of other input and output parameters in the function:
        Sends a FIN packet to the server and waits for a FIN-ACK response to close the connection.

        Returns None
        '''
        # Send FIN Packet
        finPacket = struct.pack('!HHH', 0, 0, 2) 
        client.socket.sendto(finPacket, (client.serverIP, client.serverPort))
        print("FIN packet is sent")

        # Receive FIN-ACK Packet
        finAckPacket, _ = client.socket.recvfrom(1000)
        _, _, finAckFlags = struct.unpack('!HHH', finAckPacket[:6])
        if finAckFlags & 6: 
            print("FIN-ACK packet is received")
            print("Connection closed")

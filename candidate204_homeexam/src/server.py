import socket
import struct
from datetime import datetime

class fileReceiver:
    '''
    Description:
    This class implements a "file receiver" using UDP/DRTP protocol.

    Attributes:
    serverIP (str): The IP address of the server.
    serverPort (int): The port number of the server.
    outputFile (str): The name of the file to save the received data (receive_photo.jpg).
    expectedSeq (int): The sequence number expected to be received next.
    receivedData (dict): Dictionary to store received data packets.
    socket (socket.socket): The socket object for communication.
    startTime (datetime): The start time of the data reception.
    endTime (datetime): The end time of the data reception.
    totalDataReceived (int): The total size of data received in bytes.

    Methods:
    __init__: Initializes the fileReceiver object.
    threeWayHandshake: Performs the three-way handshake protocol similar to tcp.
    start: Starts the file receiving process.
    handleSyn: Handles the SYN packet during the handshake.
    timestamp: Returns the current timestamp in a specific format.
    handleData: Handles incoming data packets.
    ack: Sends acknowledgment for received packets.
    save_data: Saves received data to the output file.
    handleFin: Handles the FIN packet to terminate the connection between server and client.
    throughput: Calculates and prints the throughput of data reception.
    '''

    def __init__(server, ip, port, discard=None):
        '''
        Description:
        Initializes the fileReceiver object with specified parameters.

        Arguments:
        ip (str): The IP address of the server.
        port (int): The port number of the server.
        discard (int): The sequence number of the packet to discard for testing purposes.

        Use of other input and output parameters in the function:
        Initializes the socket and binds it to the given IP and port. 

        Returns None but as mentioned Initializes the server
        '''
        server.discard = discard
        server.serverIP = ip
        server.serverPort = port
        server.outputFile = "received_photo.jpg"
        server.expectedSeq = 1
        server.receivedData = {}
        server.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.socket.bind((server.serverIP, server.serverPort))
        server.startTime = None
        server.endTime = None
        server.totalDataReceived = 0

        print(f"Server started at {server.serverIP} on port {server.serverPort}")

    def threeWayHandshake(server):
        '''
        Description:
        Performs the three-way handshake protocol for connection establishment between server and client

        Use of other input and output parameters in the function:
        Receives a SYN packet from the client, responds with a SYN-ACK, and waits for an ACK from the client

        Returns None, but as mention establishes a connection between server and client

        Raises:
        ConnectionError: If the expected SYN or ACK packets are not received.
        '''
        packet, clientAddress = server.socket.recvfrom(1000)
        _, _, flags = struct.unpack('!HHH', packet)
        if flags & 8:
            print("SYN packet is received")
            server.handleSyn(clientAddress)
        else:
            raise ConnectionError("First SYN was not accepted")

        packet, clientAddress = server.socket.recvfrom(1000)
        _, _, flags = struct.unpack('!HHH', packet)
        if flags & 4:
            print("ACK packet is recieved")
            return
        else:
            raise ConnectionError("First ACK was not accepted")

    def start(server) -> None:
        '''
        Description:
        Starts the file receiving process.

        Tries the three way handshake with client
        Creates the received_photo.jpg file if not already exists
        Unpacks all data from client
        Closes the connection upon receiving fin flag
        Calculates throughput 

        Returns None

        Raises:
        KeyboardInterrupt: If the server is manually interrupted with ctrl + c. 
        '''
        try:
            server.threeWayHandshake()

            with open(server.outputFile, "wb") as f:
                pass
            
            if server.startTime is None:
                server.startTime = datetime.now()

            while True:
                packet, clientAddress = server.socket.recvfrom(1000)
                _, _, flags = struct.unpack('!HHH', packet[:6])

                if flags & 2:  # FIN flag
                    print("FIN packet is received")
                    server.handleFin(clientAddress)
                    server.throughput()
                else:
                    server.handleData(packet, clientAddress)

        #Server socket closing upon termination (If server is stuck in a loop, pressing ctrl + c terminates it)
        except KeyboardInterrupt:
            server.socket.close()
            raise KeyboardInterrupt("Connection Closes")

    def handleSyn(server, clientAddress):
        '''
        Description:
        Handles the SYN packet during the handshake and sends SYN-ACK response.

        Arguments:
        clientAddress (tuple): The address of the client.
        
        Use of other input and output parameters in the function:
        Prepares and sends a SYN-ACK packet to the client to acknowledge the SYN request.

        Returns syn ack to client
        '''
        synAck = struct.pack('!HHH', 0, 0, 12)
        server.socket.sendto(synAck, clientAddress)
        print("SYN-ACK packet is sent")

    def timestamp(server):
        '''
        Description:
        Returns the current timestamp in a specific format.

        Use of other input and output parameters in the function:
        Uses the datetime module to get the current time and formats it.

        Returns:
        str: The timestamp in 'HH:MM:SS.sss' format.
        '''
        return datetime.now().strftime('%H:%M:%S.%f')[:-3]

    def handleData(server, packet, clientAddress):
        '''
        Description:
        Handles incoming data packets.

        Arguments:
        packet (bytes): The received packet data from client.
        clientAddress: The ip address of the client.

        Use of other input and output parameters in the function:
        Unpacks the packet to retrieve the sequence number, flags, and data.
        Discards the packet if its sequence number matches the discard number.
        Stores the data in receivedData if the sequence number matches the expected sequence number.
        Sends an acknowledgment for received packets.

        Returns None
        '''
        seqNum, ackNum, flags, data = struct.unpack('!HHH994s', packet)

        #if the sequence number matches the discarding number, discard this packet. 
        if seqNum == server.discard:
            server.discard = None
            print(f"Discarding {seqNum}")
            return

        #confirms the expected received packets
        if seqNum == server.expectedSeq:
            print(f"{server.timestamp()} -- packet {seqNum} is received")
            server.receivedData[seqNum] = data  # Remove padding bytes
            server.expectedSeq += 1

            # Save sequential data
            server.save_data()

            # Send ACK for received packet only if it's not already acknowledged
            if seqNum not in server.receivedData:
                server.ack(clientAddress, seqNum)

        elif seqNum < server.expectedSeq:
            # Send ACK for received packet only if it's not already acknowledged
            if seqNum not in server.receivedData:
                server.ack(clientAddress, seqNum)


    def ack(server, clientAddress, seqNum):
        '''
        Description:
        Sends acknowledgment for received packets.

        Arguments:
        clientAddress (tuple): The address of the client.
        seqNum (int): The sequence number of the received packet.

        Use of other input and output parameters in the function:
        Prepares and sends an acknowledgment packet for the received sequence number.
        Keeps track of the acknowledged packets to avoid duplicate acknowledgments.

        Returns ack for received packets
        '''
        ackPacket = struct.pack('!HHH', 0, seqNum, 4)
        server.socket.sendto(ackPacket, clientAddress)
        print(f"{server.timestamp()} -- sending ack for the received {seqNum}")

    def save_data(server):
        '''
        Description:
        Saves received data to the output file.

        Use of other input and output parameters in the function:
        Writes data to the output file in the correct order based on the sequence numbers.
        Updates the total size of data received.

        Returns the saved data in received_photo.jpg
        '''
        with open(server.outputFile, "ab") as f:
            while server.expectedSeq - 1 in server.receivedData:
                data = server.receivedData.pop(server.expectedSeq - 1)
                f.write(data)
                server.totalDataReceived += len(data)

    def handleFin(server, clientAddress):
        '''
        Description:
        Handles the FIN packet to terminate the connection.

        Arguments:
        clientAddress (tuple): The address of the client.

        Use of other input and output parameters in the function:
        Prepares and sends a FIN-ACK packet to the client to acknowledge the termination request.

        Returns fin ack to client
        '''
        finAck = struct.pack('!HHH', 0, 0, 6)
        server.socket.sendto(finAck, clientAddress)
        print("FIN-ACK packet is sent")

    def throughput(server):
        '''
        Description:
        Calculates and prints the throughput of data reception.

        Use of other input and output parameters in the function:
        Calculates the elapsed time between the start and end of data reception.
        Computes the throughput in Mbps.

        Returns Throughput
        '''
        if server.startTime:
            server.endTime = datetime.now()
            elapsedTime = (server.endTime - server.startTime).total_seconds()
            throughput = (server.totalDataReceived * 8) / (elapsedTime * 1_000_000)  # Convert to Mbps
            print(f"\nThe throughput is {throughput:.2f} Mbps")
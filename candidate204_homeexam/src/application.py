import argparse
import os
from server import fileReceiver
from client import fileSender

# Define the minimum and maximum port numbers
portMin = 1024
portMax = 65535

def portCheck(port):
    '''
    Description: 
    Checks if the provided port number is valid within the specified range.

    Arguments:
    port (str): The port number provided as a string from user.

    Returns:
    int: The validated port number as an integer.

    Raises:
    argparse.ArgumentTypeError: If the port is not an integer or is outside the valid range.
    '''
    try:
        portNum = int(port)
    except ValueError:
        raise argparse.ArgumentTypeError('Port must be an integer.')

    if portNum < portMin or portNum > portMax:
        raise argparse.ArgumentTypeError(f"Port number must be between {portMin} and {portMax}.")

    return portNum

def ipCheck(ip):
    '''
    Description:
    Validates if the provided IP address is in the correct format (dot-decimal notation).

    Arguments:
    ip (str): The IP address provided as a string.

    Returns:
    str: The validated IP address.

    Raises:
    argparse.ArgumentTypeError: If the IP address is not in the correct format or is invalid.
    '''
    split = ip.split(".") 
    if len(split) != 4:
        raise argparse.ArgumentTypeError("IP address must be in dot-decimal notation (e.g., 192.168.1.1).")
    for num in split:
        try:
            if not 0 <= int(num) <= 255:
                raise argparse.ArgumentTypeError("Each part of the IP address must be between 0 and 255.")
        except ValueError:
             raise argparse.ArgumentTypeError("IP address should only contain numbers and dots.")
        
    return ip

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Data Transfer using DRTP", epilog="end of help message.")
    parser.add_argument('-s', '--server', action='store_true', help="Use to run in server mode.")
    parser.add_argument('-c', '--client', action='store_true', help="Use to run in client mode.")
    parser.add_argument('-p', '--port', type=portCheck, default=8088, help="Choose port number to bind/connect to (default: 8088).")
    parser.add_argument('-i', '--ip', type=ipCheck, default="127.0.0.1", help="Choose IP address to bind/connect to (default: 127.0.0.1).")
    parser.add_argument('-f', '--file', type=str, help="Path to the JPG file to send (required in client mode).")
    parser.add_argument('-w', '--window', type=int, default=3, help="Size of the sliding window for packet transmission (default: 3).")
    parser.add_argument('-d', '--discard', type=int, default=None, help="Packet sequence number to discard for testing purposes.")

    args = parser.parse_args()
    
    # Ensuring that the user doesnt start server- and client mode at the same time
    if args.server and args.client:
        parser.error("Cannot run in both server and client modes simultaneously.")
    
    #Ensuring that the user has to choose either server or client mode
    if not args.server and not args.client:
        parser.error("Must specify either server or client mode.")
    
    # Running the server mode
    if args.server:
        server = fileReceiver(args.ip, args.port, args.discard)
        server.start()
    
    # Running the client mode
    elif args.client:
        #If user doesnt provide with a file to send
        if not args.file:
            parser.error("File path must be provided in client mode.")
        #If user provides with a file that doesnt exist
        if not os.path.exists(args.file):
            raise argparse.ArgumentTypeError(f"File does not exist.")
        client = fileSender(args.ip, args.port, args.file, args.window)
        client.start()

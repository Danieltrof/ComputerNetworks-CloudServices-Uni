from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink


class LinuxRouter( Node ):
    """A Node with IP forwarding enabled.
    Means that every packet that is in this node, comunicate freely with its interfaces."""

    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()


class NetworkTopo( Topo ):

    def build( self, **_opts ):		
        h1=self.addHost("h1",ip=None)
        r=self.addNode("r",cls=LinuxRouter,ip=None)
        h2=self.addHost("h2",ip=None)
        self.addLink(h1,r,params1={ 'ip' : '10.0.0.1/24' },params2={ 'ip' : '10.0.0.2/24' })#,max_queue_size=834, use_htb=True)
        self.addLink(r,h2,params1={ 'ip' : '10.0.1.1/24' },params2={ 'ip' : '10.0.1.2/24' }) #, bw=100, delay='25ms')#, max_queue_size=834, use_htb=True)

topo = NetworkTopo()
net = Mininet( topo=topo, link=TCLink )
net.start()

#ip route add ipA via ipB dev INTERFACE
#every packet going to ipA must first go to ipB using INTERFACE
net["h1"].cmd("ip route add 10.0.1.2 via 10.0.0.2 dev h1-eth0")
net["h2"].cmd("ip route add 10.0.0.1 via 10.0.1.1 dev h2-eth0")
#this command is just to r3 ping r2 work, because it will use the correct ip
net["h2"].cmd("ip route add 10.0.0.2 via 10.0.1.1 dev h2-eth0")

# this adds a delay of 100ms - if you ping h2 from h1, the RTT will be 100ms 
#net["r"].cmd("tc qdisc add dev r-eth1 root netem delay 200ms")
net["r"].cmd("tc qdisc add dev r-eth1 root netem delay 100ms loss 5%")

net["h1"].cmd("ethtool -K h1-eth0 tso off")
net["h1"].cmd("ethtool -K h1-eth0 gso off")
net["h1"].cmd("ethtool -K h1-eth0 lro off")
net["h1"].cmd("ethtool -K h1-eth0 gro off")
net["h1"].cmd("ethtool -K h1-eth0 ufo off")


net["h2"].cmd("ethtool -K h2-eth0 tso off")
net["h2"].cmd("ethtool -K h2-eth0 gso off")
net["h2"].cmd("ethtool -K h2-eth0 lro off")
net["h2"].cmd("ethtool -K h2-eth0 gro off")
net["h2"].cmd("ethtool -K h2-eth0 ufo off")



net.pingAll()
CLI( net )
net.stop()
#!/usr/bin/python
#
# Script to generate "CE" (r2) rib-groups/routing-instances configuration
#

from string import Template
from netaddr import IPAddress, IPNetwork

t = Template("""
set interfaces ge-0/0/3.$id vlan-id $id family inet address $ipv4_local/31
set interfaces ge-0/0/3.$id vlan-id $id family inet6 address $ipv6_local/127
set interfaces lo0.$id family inet address 100.64.$id.1/32
set interfaces lo0.$id family inet6 address 2001:164:$id::1/128
set routing-instances CE-$id instance-type virtual-router
set routing-instances CE-$id interface lo0.$id
set routing-instances CE-$id interface ge-0/0/3.$id
set routing-instances CE-$id routing-options autonomous-system 10$id independent-domain
set routing-instances CE-$id routing-options static route 100.64.$id.0/24 discard
set routing-instances CE-$id routing-options rib CE-$id.inet6.0 static route 2001:164:$id::/48 discard
set routing-instances CE-$id protocols bgp group ebgp type external peer-as 111 neighbor $ipv4_remote family inet
set routing-instances CE-$id protocols bgp group ebgp type external peer-as 111 neighbor $ipv6_remote family inet6
set routing-instances CE-$id protocols bgp group ebgp export PS-EBGP-EXPORT
""")

ip4loc = IPAddress('172.20.3.1')
ip6loc = IPAddress('2001:200:20:3::1')

for i in range(10,200):
    ip4rem = ip4loc - 1
    ip6rem = ip6loc - 1
    output = t.substitute(id=str(i),
                          ipv4_local=str(ip4loc),
                          ipv6_local=str(ip6loc),
                          ipv4_remote=str(ip4rem),
                          ipv6_remote=str(ip6rem))
    print output
    ip4loc += 2
    ip6loc += 2

                        

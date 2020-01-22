#!/usr/bin/python

from string import Template
from netaddr import IPAddress, IPNetwork

t = Template("""
set interfaces ge-0/0/3.$id vlan-id $id family inet address $ipv4_local/31
set interfaces ge-0/0/3.$id vlan-id $id family inet6 address $ipv6_local/127
set interfaces lo0.$id family inet address 100.111.$id.1/32
set interfaces lo0.$id family inet6 address 2001:111:$id::1/128
set interfaces lo0.0 family inet address 100.100.$id.1/32
set interfaces lo0.0 family inet6 address 2001:1100:$id::1/128
set routing-options interface-routes rib-group inet RG-INET0-TO-VRs
set routing-options interface-routes rib-group inet6 RG-INET6-TO-VRs
set routing-instances VR$id instance-type virtual-router
set routing-instances VR$id interface lo0.$id
set routing-instances VR$id interface ge-0/0/3.$id
set routing-instances VR$id routing-options interface-routes rib-group inet RG-VR$id-TO-INET0
set routing-instances VR$id routing-options interface-routes rib-group inet6 RG-VR$id-TO-INET6
set routing-instances VR$id routing-options static route 100.111.$id.0/24 discard
set routing-instances VR$id routing-options rib VR$id.inet6.0 static route 2001:111:$id::/48 discard
set routing-instances VR$id protocols bgp group ebgp type external peer-as 10$id neighbor $ipv4_remote family inet unicast rib-group RG-VR$id-TO-INET0
set routing-instances VR$id protocols bgp group ebgp type external peer-as 10$id neighbor $ipv6_remote family inet6 unicast rib-group RG-VR$id-TO-INET6
set routing-instances VR$id protocols bgp group ebgp export PS-EBGP-EXPORT
set policy-options as-path AS10$id ".* (10$id)"
set policy-options policy-statement PS-VR$id-TO-INET0 term BGP from protocol bgp
set policy-options policy-statement PS-VR$id-TO-INET0 term BGP from as-path AS10$id
set policy-options policy-statement PS-VR$id-TO-INET0 term BGP then accept
set policy-options policy-statement PS-VR$id-TO-INET0 term DIRECT from protocol direct
set policy-options policy-statement PS-VR$id-TO-INET0 term DIRECT from interface lo0.$id
set policy-options policy-statement PS-VR$id-TO-INET0 term DIRECT then accept
set policy-options policy-statement PS-VR$id-TO-INET0 then reject
set policy-options policy-statement PS-INET0-TO-VRs term VR$id-INET from protocol direct
set policy-options policy-statement PS-INET0-TO-VRs term VR$id-INET from family inet
set policy-options policy-statement PS-INET0-TO-VRs term VR$id-INET from route-filter 100.100.$id.1/32 exact
set policy-options policy-statement PS-INET0-TO-VRs term VR$id-INET to rib VR$id.inet.0
set policy-options policy-statement PS-INET0-TO-VRs term VR$id-INET then accept
set policy-options policy-statement PS-INET0-TO-VRs term VR$id-INET from protocol direct
set policy-options policy-statement PS-INET0-TO-VRs term VR$id-INET6 from family inet6
set policy-options policy-statement PS-INET0-TO-VRs term VR$id-INET6 from route-filter 2001:1100:$id::1/128 exact
set policy-options policy-statement PS-INET0-TO-VRs term VR$id-INET6 to rib VR$id.inet6.0
set policy-options policy-statement PS-INET0-TO-VRs term VR$id-INET6 then accept
""")

ip4loc = IPAddress('172.20.3.0')
ip6loc = IPAddress('2001:200:20:3::0')

rg4 = 'set routing-options rib-groups RG-INET0-TO-VRs import-rib [ inet.0'
rg6 = 'set routing-options rib-groups RG-INET6-TO-VRs import-rib [ inet6.0'
for i in range(10,200):
    rg4 += ' VR' + str(i) + '.inet.0'
    rg6 += ' VR' + str(i) + '.inet6.0'
rg4 += ' ] import-policy PS-INET0-TO-VRs'
rg6 += ' ] import-policy PS-INET0-TO-VRs'
print rg4
print rg6 

for i in range(10,200):
    rg4 = 'set routing-options rib-groups RG-VR'+str(i)+'-TO-INET0 import-rib [ VR'+str(i)+'.inet.0 inet.0 ] import-policy PS-VR'+str(i)+'-TO-INET0'
    rg6 = 'set routing-options rib-groups RG-VR'+str(i)+'-TO-INET6 import-rib [ VR'+str(i)+'.inet6.0 inet6.0 ] import-policy PS-VR'+str(i)+'-TO-INET0'
    print rg4
    print rg6 

for i in range(10,200):
    ip4rem = ip4loc + 1
    ip6rem = ip6loc + 1
    output = t.substitute(id=str(i),
                          ipv4_local=str(ip4loc),
                          ipv6_local=str(ip6loc),
                          ipv4_remote=str(ip4rem),
                          ipv6_remote=str(ip6rem))
    print output
    ip4loc += 2
    ip6loc += 2

print 'set policy-options policy-statement PS-INET0-TO-VRs then reject'                        

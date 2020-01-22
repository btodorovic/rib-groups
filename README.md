
# VMM TOPOLOGY ILLUSTRATING 'rib-groups' FEATURE

## TOPOLOGY

<pre>
+----+                       +----+
|    |----- ge-0/0/3.10 -----|    |  - Each IFL on ge-0/0/3 belongs to a separate virtual-router @ r1, r2:
|    |----- ge-0/0/3.11 -----|    |      - r1: routing-instances VR10 upto VR199
| r1 |          ...          | r2 |      - r2: routing-instances CE-10 upto CE-199
|    |                       |    |  - RIs @ r2 - are very simple, basic, emulating CE routers (no rib-groups there)
|    |----- ge-0/0/3.199 ----|    |  - RIs @ r1 - emulate a PE with VRs and rib-groups defined
+----+                       +----+
</pre>

### Router Configurations and Sample Outputs

* [r1.full.conf](r1 - full configuration)
* [r2.full.conf](r2 - full configuration)
* [sample-outputs.txt](Sample CLI outputs)


## JUNOS RIBs

Since Day One the routing tables on the Juniper Networks routers and switches have been designed in a "compartmental"
fashion, intended to store routing information belonging to different routing contexts. This design came hand in hand
with the technical requirement to implement MPLS L3 VPNs and similar applications back in 1998 when MPLS technology
was born. Therefore, Juniper Networks devices can maintain a myriad of independent routing tables, both on the
Routing Engine (RE) and on the Packet Forwarding Engine (PFE). We refer the former as Routing Information Base (RIB),
while the latter is somtimes referred to as Forwarding Information Base (FIB).

When a "virgin" router is booted it comes only with one single RIB - the default **inet.0**, used to carry IPv4
unicast prefixes. When MPLS services are activated on the box, the router gets two additional RIBs - **mpls.0**
used to store MPLS label forwarding information and **inet.3** used as a helper RIB to store MPLS LSP endpoints,
used by various MPLS services to retrieve the next-hops for their operation. Finally, if IPv6 is used, **inet6.0**
RIB appears in there as well. If IS-IS is used as IGP **iso.0** RIB will appear to carry CLNS routing information.
If MPLS IPv4 VPNs are used **bgp.l3vpn.0** RIB will be there to store BGP-learnt VPNv4 routes.
If MPLS IPv6 VPNs are used **bgp.l3vpn-inet6.0** RIB will be there to store BGP-learnt VPNv6 routes.

Aside of RIBs, to implement various VPN services, Junos OS uses the concept of Routing Instances (RI).
The defualt Junos RIB **inet.0**, as well as **inet6.0**, **inet.3** etc. belong to the Master (Default) RI.
A Routing Instance is, thus, a collection of RIBs storing routing information relevant for them.
When a VPN needs to be defined, Junos OS creates a new Routing Instance with a defined name (e.g. VPN).
The VPN routing instance is simply a collection of RIBs - **VPN.inet.0**, **VPN.inet6.0** etc.

Routing information can be exchnaged among routing instances using the RIB Group mehanism, shown here.

## RIB Group Definitions

Simple exercise showing the power of rib-groups and their replications:
* We created two sets of RIB Groups.
* The first RG set consists of 2 RGs, used to copy prefixes from default RI into VRxxx RIs:
    - **RG-INET0-TO-VRs** - copies **inet.0** prefixes into **VRxxx.inet.0** (IPv4)
    - **RG-INET6-TO-VRs** - copies **inet6.0** prefixes into **VRxxx.inet6.0** (IPv6)
    - Both use import-policy **PS-INET0-TO-VRs** to copy only one loopback address (100.100.$vrid$.1/32), defined on lo0.0
    - The "to" clause in the policy terms is used to ensure prefix import into the right routing instance.
* The second RG set conists of 200 RGs, used to copy prefixes form VRxxx RIs into the default RI:
    - **RG-VRxxx-TO-INET0** - copies **VRxxx.inet.0** prefixes into **inet.0** (IPv4)
    - **RG-VRxxx-TO-INET0** - copies **VRxxx.inet6.0** prefixes into **inet6.0** (IPv6)
    - All use import-policy **PS-VR100-TO-INET0** copying only direct and BGP routes

Once the RIB Groups are defined they do nothing. They serve simply as "templates" signaling the router our intention
to copy prefixes from one RIB into the other. However, in order for them to take this action, they must be applied
within the proper routing protocol configuration context.

## RIB Group Applications

RGs are applied under the appropriate routing protocol configurations. The place where they are applied depends on
the routing protocol context where the routes are imported from. Remember that routing information import / export
operations in the Junos OS are "RIB-centric" - i.e. they are defined with the RIB being the reference point. In other
words, prefixes are always:

* **IMPORTED FROM** an external source (e.g. routing protocol) or another RIB **INTO** the current RIB, or:
* **EXPORTED INTO** an external source (e.g. routing protocol) or another RIB **INTO** the current RIB.

In this sense, we always apply the RIB group at the appropriate routing protocol context where we need to import
the prefixes from the routing protocol process into the RIB Group:

* If the RG imports routes from the Default RI (**inet.0** RIB), it MUST be applied at the Default RI routing protocol level - e.g.:
  - Direct routes: [edit routing-options interface-groups rib-group]
  - Static routes: [edit routing-options static rib-group]
  - ISIS/OSPF: [edit protocols isis/ospf rib-group]
  - BGP: [edit protocols bgp group GROUP family AFI rib-group]

* If the RG imports routes from a non-default RI (**RI.inet.0** RIB), it MUST be applied at the appropriate RI routing protocol level.
  - Direct routes: [edit routing-instances RI routing-options interface-groups rib-group]
  - Static routes: [edit routing-instances RI routing-options static rib-group]
  - ISIS/OSPF: [edit routing-instances RI protocols isis/ospf rib-group]
  - BGP: [edit routing-instances RI protocols bgp group GROUP family AFI rib-group]

In other words:

<pre>
# Default routing-instance
routing-options {
    interface-routes {
        rib-group {
            inet RG-INET0-TO-VRs;    # Copies IPv4 interface routes (protocol direct) from inet.0 into VRxxx.inet.0
            inet6 RG-INET6-TO-VRs;   # Copies IPv6 interface routes (protocol direct) from inet6.0 into VRxxx.inet6.0
        }
    }
}

routing-instances {
    VRxxx {
        routing-options {
            interface-routes {
                rib-group {
                    inet RG-VR10-TO-INET0;  # Copies IPv4 interface routes (protocol direct) from VRxxx.inet.0 into inet.0
                    inet6 RG-VR10-TO-INET6; # Copies IPv6 interface routes (protocol direct) from VRxxx.inet6.0 into inet6.0
                }
            }
        }
        protocols {
            bgp {
                group ebgp {
                    type external;
                    export PS-EBGP-EXPORT;
                    peer-as 1010;
                    neighbor 172.20.3.1 {
                        family inet {
                            unicast {
                                rib-group RG-VR10-TO-INET0; # Copies BGP IPv4 routes (protocol bgp) from VR into default RI
                            }
                        }
                    }
                    neighbor 2001:200:20:3::1 {
                        family inet6 {
                            unicast {
                                rib-group RG-VR10-TO-INET6; # Copies BGP IPv6 routes (protocol bgp) from VR into default RI
                            }
                        }
                    }
                }
            }
        }
    }
}
</pre>


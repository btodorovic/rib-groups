
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

* [r1 configuration](r1.full.conf)
* [r2 configuration](r2.full.conf)
* [Sample CLI outputs](sample-outputs.txt)
* [VMM/Junosphere configuration file](vm.conf)
* [gen-pe.cy](gen-pe.cy) - script to generate **r1** configuration
* [gen-ce.cy](gen-ce.cy) - script to generate **r2** configuration

## Theory - RIBs, Routing Instances, Logical Systems

Since Day One the routing tables on the Juniper Networks routers and switches have been designed in a "compartmental"
fashion, intended to store routing information belonging to different routing contexts. This design came hand in hand
with the technical requirement to implement MPLS L3 VPNs and similar applications back in 1998 when MPLS technology
was born. Therefore, Juniper Networks devices can maintain a myriad of independent routing tables, both on the
Routing Engine (RE) and on the Packet Forwarding Engine (PFE). We refer the former as Routing Information Base (RIB),
while the latter is somtimes referred to as Forwarding Information Base (FIB). The full story about routing tables in
the Junos OS you can find on the
[Understanding Junos OS Routing Tables](https://www.juniper.net/documentation/en_US/junos/topics/concept/routing-tables-understanding.html) documentation page.

When a "virgin" router is booted it comes only with one single RIB created on the RE - the default **inet.0**,
used to carry IPv4 unicast prefixes. In the PFE the router has a pre-ccreated "FIB" **default.inet**. When
multicast is used on the router, **inet.1** RIB will be created, to store multicst (S,G) pairs, as well as **inet.2**
to store prefixes used by multicast RPF checks. When MPLS services are activated on the box, the router gets two
additional RIBs - **mpls.0** used to store MPLS label forwarding information and **inet.3** used as a helper RIB to
store MPLS LSP endpoints, used by various MPLS services to retrieve the next-hops for their operation. Finally,
if IPv6 is used, **inet6.0** RIB appears in there as well. If IS-IS is used as IGP **iso.0** RIB will appear to
carry CLNS routing information. If MPLS IPv4 VPNs are used **bgp.l3vpn.0** RIB will be there to store BGP-learnt
VPNv4 routes. If MPLS IPv6 VPNs are used **bgp.l3vpn-inet6.0** RIB will be there to store BGP-learnt VPNv6 routes.
The rest of the story you can find [here](https://www.juniper.net/documentation/en_US/junos/topics/concept/routing-tables-understanding.html).

A simplified part of the story above is shown in the picture below:
<pre>
                                                      
        MASTER/DEFAULT ROUTING INSTANCE            NON-DEFAULT ROUTING INSTANCES (VRF, VR etc.)
        ===============================            ============================================
                         _____________                                     
                        /             \                                                               
                       (  bgp.l3vpn.0  )          +--------------------+  +--------------------+
                        \_____________/           !    INSTANCE "A"    !  !    INSTANCE "B"    !
                                                  !                    !  !                    !
                 ___________      ___________     !  +------------+    !  !  +------------+    !
                /           \    /           \    !  |  A.inet6.0 |    !  !  |  B.inet6.0 |    !
               (   inet.3    )  (  inet6.3    )   !  +------------+    !  !  +------------+    !
                \___________/    \___________/    !                    !  !                    !
                                                  !  +------------+    !  !  +------------+    !
 +----------+   +------------+   +------------+   !  |  A.inet.0  |    !  !  |  B.inet.0  |    !
 |  mpls.0  |   |   inet.0   |   |  inet6.0   |   !  +------------+    !  !  +------------+    !
 +----------+   +------------+   +------------+   +--------------------+  +--------------------+ CONTROL
                                                                                                 PLANE (RE)
============================================================================================================
 +----------+ +---------------+ +---------------+   +-------------+          +-------------+     FORWARDING
 |  mpls.0  | | default.inet  | | default.inet6 |   |   A.inet6   |          |   B.inet6   |     PLANE (PFE)
 +----------+ +---------------+ +---------------+   +-------------+          +-------------+
                                                    +-------------+          +-------------+
                                                    |   A.inet    |          |   B.inet    |
                                                    +-------------+          +-------------+
</pre>

Aside of RIBs, to implement various VPN services, Junos OS uses the concept of [Routing Instances (RI)](https://www.juniper.net/documentation/en_US/junos/topics/concept/routing-instances-overview.html).
A Routing Instance is simply a collection of RIBs storing routing information relevant for them.
The defualt Junos RIB **inet.0**, as well as **inet6.0**, **inet.3** etc. belong to the Master (Default) RI.
When a VPN needs to be defined, Junos OS creates a new Routing Instance with a defined name (e.g. VPN).
The VPN routing instance is simply a collection of RIBs - **VPN.inet.0**, **VPN.inet6.0** etc.

As of Junos OS Release 8, a concept of [Logical Systems](https://www.juniper.net/documentation/en_US/junos/topics/topic-map/security-logical-systems-for-routers-and-switches.html)
has been introduced. Logical systems are used to partition a single physical router into a number of logical partitions.
Although logical systems are similar to Virtual Routers, they are implemented in a slightly different way. Unlike Virtual
Routers, VRFs and other types of routing instances, which operate within the common Routing Protocol Daemon (rpd) process,
creation of a Logical System starts a separate instance of rpd - e.g.:

<pre>
logical-systems {
   LS-1;
   LS-2;
   LS-3;
}

root@r1> start shell
root@r1:~ # ps ax | grep rpd
 6520  -  S        7:24.04 /usr/sbin/rpd -N
89997  -  S        0:00.42 /usr/sbin/rpd -N -JLLS-1
89998  -  S        0:00.42 /usr/sbin/rpd -N -JLLS-2
89999  -  S        0:00.41 /usr/sbin/rpd -N -JLLS-3
</pre>

There can be up to 15 Logical Systems defined within the same physical router.

Each LS may have its own set of routing instances, each routing instance being a collection of RIBs.

Routing information can be exchnaged among routing instances using the RIB Group mehanism, discussed later.
If Logical Systems are used, RIBs can exchange routing information among themselves only if they belong to the
same Logical System. RIBs belonging to different Logical Systems cannot exchange routing information directly
using RIB Groups. They can only exchange routing information by connecting two Logical Systems together
(either via a physical "hairpin" or a logical tunnel (LT) interface).

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

Simplified, the syntax looks like this:
<pre>
routing-options {
   rib-groups {
        RG-INET0-TO-VRs {
            import-rib [ inet.0 VR10.inet.0 VR11.inet.0 ... VR199.inet.0 ];
            import-policy PS-INET0-TO-VRs;
        }
        RG-VR10-TO-INET0 {
            import-rib [ VR10.inet.0 inet.0 ];
            import-policy PS-VR10-TO-INET0;
        }
        RG-VR10-TO-INET6 {
            import-rib [ VR10.inet6.0 inet6.0 ];
            import-policy PS-VR10-TO-INET0;
        }
        ...
        RG-VR199-TO-INET0 {
            import-rib [ VR199.inet.0 inet.0 ];
            import-policy PS-VR199-TO-INET0;
        }
        RG-VR199-TO-INET6 {
            import-rib [ VR199.inet6.0 inet6.0 ];
            import-policy PS-VR199-TO-INET0;
        }
    }
}

policy-options {
    policy-statement PS-INET0-TO-VRs {
        term VR10-INET {
            from {
                family inet;
                protocol direct;
                route-filter 100.100.10.1/32 exact;
            }
            to rib VR10.inet.0;
            then accept;
        }
        term VR10-INET6 {
            from {
                family inet6;
                route-filter 2001:1100:10::1/128 exact;
            }
            to rib VR10.inet6.0;
            then accept;
        }
        term VR11-INET {
            from {
                family inet;
                protocol direct;
                route-filter 100.100.11.1/32 exact;
            }
            to rib VR11.inet.0;
            then accept;
        }
        term VR11-INET6 {
            from {
                family inet6;
                route-filter 2001:1100:11::1/128 exact;
            }
            to rib VR11.inet6.0;
            then accept;
        }
        ... (etc) ...
    }
    policy-statement PS-VR10-TO-INET0 {
        term BGP {
            from {
                protocol bgp;
                as-path AS1010;
            }
            then accept;
        }
        term DIRECT {
            from {
                protocol direct;
                interface lo0.10;
            }
            then accept;
        }
        then reject;
    }
    ... (etc) ...
}
</pre>

See the full router configurations for more details:
* [r1 configuration](r1.full.conf)
* [r2 configuration](r2.full.conf)

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

See the full router configurations for more details:
* [r1 configuration](r1.full.conf)
* [r2 configuration](r2.full.conf)

Last, but not the least - RIB groups can also be created within Logical Systems. Same principles apply.

## RIB Groups Troubleshooting

Standard operational commands may be used to check if the prefixes are copied properly from one RIB to another:

<pre>

root@r1> show route table VR21.inet.0 

VR21.inet.0: 6 destinations, 6 routes (6 active, 0 holddown, 0 hidden)
+ = Active Route, - = Last Active, * = Both

100.64.21.0/24     *[BGP/170] 01:19:16, localpref 100
                      AS path: 1021 I, validation-state: unverified
                    > to 172.20.3.23 via ge-0/0/3.21
100.100.21.1/32    *[Direct/0] 01:18:16
                    > via lo0.0
100.111.21.0/24    *[Static/5] 01:27:34
                      Discard
100.111.21.1/32    *[Direct/0] 01:27:33
                    > via lo0.21
172.20.3.22/31     *[Direct/0] 01:27:33
                    > via ge-0/0/3.21
172.20.3.22/32     *[Local/0] 01:27:33
                      Local via ge-0/0/3.21

root@r1> show route table VR31.inet.0 

VR31.inet.0: 6 destinations, 6 routes (6 active, 0 holddown, 0 hidden)
+ = Active Route, - = Last Active, * = Both

100.64.31.0/24     *[BGP/170] 01:19:38, localpref 100
                      AS path: 1031 I, validation-state: unverified
                    > to 172.20.3.43 via ge-0/0/3.31
100.100.31.1/32    *[Direct/0] 01:18:25
                    > via lo0.0
100.111.31.0/24    *[Static/5] 01:27:43
                      Discard
100.111.31.1/32    *[Direct/0] 01:27:42
                    > via lo0.31
172.20.3.42/31     *[Direct/0] 01:27:42
                    > via ge-0/0/3.31
172.20.3.42/32     *[Local/0] 01:27:42
                      Local via ge-0/0/3.31

root@r1> show route 100.100.21.1/32 

inet.0: 584 destinations, 584 routes (584 active, 0 holddown, 0 hidden)
+ = Active Route, - = Last Active, * = Both

100.100.21.1/32    *[Direct/0] 01:21:06
                    > via lo0.0

VR21.inet.0: 6 destinations, 6 routes (6 active, 0 holddown, 0 hidden)
+ = Active Route, - = Last Active, * = Both

100.100.21.1/32    *[Direct/0] 01:18:51
                    > via lo0.0

root@r1> show route 100.100.21.1/32 detail

inet.0: 584 destinations, 584 routes (584 active, 0 holddown, 0 hidden)
100.100.21.1/32 (1 entry, 0 announced)
        *Direct Preference: 0
                Next hop type: Interface, Next hop index: 0
                Address: 0xb6335b0
                Next-hop reference count: 2
                Next hop: via lo0.0, selected
                State: <Active Int>
                Local AS:   111 
                Age: 1:21:08 
                Validation State: unverified 
                Task: IF
                AS path: I 
                Secondary Tables: VR21.inet.0

VR21.inet.0: 6 destinations, 6 routes (6 active, 0 holddown, 0 hidden)

100.100.21.1/32 (1 entry, 1 announced)
        *Direct Preference: 0
                Next hop type: Interface, Next hop index: 0
                Address: 0xb6335b0
                Next-hop reference count: 2
                Next hop: via lo0.0, selected
                State: <Secondary Active Int>
                Local AS:   111 
                Age: 1:18:53 
                Validation State: unverified 
                Task: IF
                Announcement bits (1): 1-KRT 
                AS path: I 
                Primary Routing Table inet.0

root@r1> show route 100.100.31.1/32

inet.0: 584 destinations, 584 routes (584 active, 0 holddown, 0 hidden)
+ = Active Route, - = Last Active, * = Both

100.100.31.1/32    *[Direct/0] 01:31:07
                    > via lo0.0

VR31.inet.0: 6 destinations, 6 routes (6 active, 0 holddown, 0 hidden)
+ = Active Route, - = Last Active, * = Both

100.100.31.1/32    *[Direct/0] 01:28:52
                    > via lo0.0

root@r1> show route 100.100.31.1/32 detail

inet.0: 584 destinations, 584 routes (584 active, 0 holddown, 0 hidden)
100.100.31.1/32 (1 entry, 0 announced)
        *Direct Preference: 0
                Next hop type: Interface, Next hop index: 0
                Address: 0xb633970
                Next-hop reference count: 2
                Next hop: via lo0.0, selected
                State: <Active Int>
                Local AS:   111
                Age: 1:31:09
                Validation State: unverified
                Task: IF
                AS path: I
                Secondary Tables: VR31.inet.0

VR31.inet.0: 6 destinations, 6 routes (6 active, 0 holddown, 0 hidden)

100.100.31.1/32 (1 entry, 1 announced)
        *Direct Preference: 0
                Next hop type: Interface, Next hop index: 0
                Address: 0xb633970
                Next-hop reference count: 2
                Next hop: via lo0.0, selected
                State: <Secondary Active Int>
                Local AS:   111
                Age: 1:28:54
                Validation State: unverified
                Task: IF
                Announcement bits (1): 1-KRT
                AS path: I
                Primary Routing Table inet.0

root@r1> show route 2001:1100:21::1/128

inet6.0: 585 destinations, 775 routes (585 active, 0 holddown, 0 hidden)
+ = Active Route, - = Last Active, * = Both

2001:1100:21::1/128*[Direct/0] 01:34:30
                    > via lo0.0

VR21.inet6.0: 9 destinations, 9 routes (9 active, 0 holddown, 0 hidden)
+ = Active Route, - = Last Active, * = Both

2001:1100:21::1/128*[Direct/0] 01:32:15
                    > via lo0.0

root@r1> show route 2001:1100:21::1/128 detail

inet6.0: 585 destinations, 775 routes (585 active, 0 holddown, 0 hidden)
2001:1100:21::1/128 (1 entry, 0 announced)
        *Direct Preference: 0
                Next hop type: Interface, Next hop index: 0
                Address: 0xb637db0
                Next-hop reference count: 2
                Next hop: via lo0.0, selected
                State: <Active Int>
                Local AS:   111
                Age: 1:34:32
                Validation State: unverified
                Task: IF
                AS path: I
                Secondary Tables: VR21.inet6.0

VR21.inet6.0: 9 destinations, 9 routes (9 active, 0 holddown, 0 hidden)

2001:1100:21::1/128 (1 entry, 1 announced)
        *Direct Preference: 0
                Next hop type: Interface, Next hop index: 0
                Address: 0xb637db0
                Next-hop reference count: 2
                Next hop: via lo0.0, selected
                State: <Secondary Active Int>
                Local AS:   111
                Age: 1:32:17
                Validation State: unverified
                Task: IF
                Announcement bits (1): 1-KRT
                AS path: I
                Primary Routing Table inet6.0

root@r1> show route 2001:1100:31::1/128

inet6.0: 585 destinations, 775 routes (585 active, 0 holddown, 0 hidden)
+ = Active Route, - = Last Active, * = Both

2001:1100:31::1/128*[Direct/0] 01:34:38
                    > via lo0.0

VR31.inet6.0: 9 destinations, 9 routes (9 active, 0 holddown, 0 hidden)
+ = Active Route, - = Last Active, * = Both

2001:1100:31::1/128*[Direct/0] 01:32:23
                    > via lo0.0

root@r1> show route 2001:1100:31::1/128 detail

inet6.0: 585 destinations, 775 routes (585 active, 0 holddown, 0 hidden)
2001:1100:31::1/128 (1 entry, 0 announced)
        *Direct Preference: 0
                Next hop type: Interface, Next hop index: 0
                Address: 0xb638170
                Next-hop reference count: 2
                Next hop: via lo0.0, selected
                State: <Active Int>
                Local AS:   111
                Age: 1:34:41
                Validation State: unverified
                Task: IF
                AS path: I
                Secondary Tables: VR31.inet6.0

VR31.inet6.0: 9 destinations, 9 routes (9 active, 0 holddown, 0 hidden)

2001:1100:31::1/128 (1 entry, 1 announced)
        *Direct Preference: 0
                Next hop type: Interface, Next hop index: 0
                Address: 0xb638170
                Next-hop reference count: 2
                Next hop: via lo0.0, selected
                State: <Secondary Active Int>
                Local AS:   111
                Age: 1:32:26
                Validation State: unverified
                Task: IF
                Announcement bits (1): 1-KRT
                AS path: I
                Primary Routing Table inet6.0

root@r1> show route 100.64.31.0/24 detail

inet.0: 584 destinations, 584 routes (584 active, 0 holddown, 0 hidden)
100.64.31.0/24 (1 entry, 1 announced)
        *BGP    Preference: 170/-101
                Next hop type: Router, Next hop index: 7000
                Address: 0xfd647d0
                Next-hop reference count: 4
                Source: 172.20.3.43
                Next hop: 172.20.3.43 via ge-0/0/3.31, selected
                Session Id: 0x2eb
                State: <Secondary Active Ext>
                Peer AS:  1031
                Age: 1:34:22
                Validation State: unverified
                Task: BGP_1031.172.20.3.43+62813
                Announcement bits (2): 0-KRT 2-BGP_RT_Background
                AS path: 1031 I
                Accepted
                Localpref: 100
                Router ID: 100.64.31.1
                Primary Routing Table VR31.inet.0

VR31.inet.0: 6 destinations, 6 routes (6 active, 0 holddown, 0 hidden)

100.64.31.0/24 (1 entry, 1 announced)
        *BGP    Preference: 170/-101
                Next hop type: Router, Next hop index: 7000
                Address: 0xfd647d0
                Next-hop reference count: 4
                Source: 172.20.3.43
                Next hop: 172.20.3.43 via ge-0/0/3.31, selected
                Session Id: 0x2eb
                State: <Active Ext>
                Peer AS:  1031
                Age: 1:34:22
                Validation State: unverified
                Task: BGP_1031.172.20.3.43+62813
                Announcement bits (1): 1-KRT
                AS path: 1031 I
                Accepted
                Localpref: 100
                Router ID: 100.64.31.1
                Secondary Tables: inet.0

root@r1> show route 100.64.21.0/24

inet.0: 584 destinations, 584 routes (584 active, 0 holddown, 0 hidden)
+ = Active Route, - = Last Active, * = Both

100.64.21.0/24     *[BGP/170] 01:34:21, localpref 100
                      AS path: 1021 I, validation-state: unverified
                    > to 172.20.3.23 via ge-0/0/3.21

VR21.inet.0: 6 destinations, 6 routes (6 active, 0 holddown, 0 hidden)
+ = Active Route, - = Last Active, * = Both

100.64.21.0/24     *[BGP/170] 01:34:21, localpref 100
                      AS path: 1021 I, validation-state: unverified
                    > to 172.20.3.23 via ge-0/0/3.21

root@r1> show route 100.64.21.0/24 detail

inet.0: 584 destinations, 584 routes (584 active, 0 holddown, 0 hidden)
100.64.21.0/24 (1 entry, 1 announced)
        *BGP    Preference: 170/-101
                Next hop type: Router, Next hop index: 7054
                Address: 0xfd6d770
                Next-hop reference count: 4
                Source: 172.20.3.23
                Next hop: 172.20.3.23 via ge-0/0/3.21, selected
                Session Id: 0x394
                State: <Secondary Active Ext>
                Peer AS:  1021
                Age: 1:34:24
                Validation State: unverified
                Task: BGP_1021.172.20.3.23+179
                Announcement bits (2): 0-KRT 2-BGP_RT_Background
                AS path: 1021 I
                Accepted
                Localpref: 100
                Router ID: 100.64.21.1
                Primary Routing Table VR21.inet.0

VR21.inet.0: 6 destinations, 6 routes (6 active, 0 holddown, 0 hidden)

100.64.21.0/24 (1 entry, 1 announced)
        *BGP    Preference: 170/-101
                Next hop type: Router, Next hop index: 7054
                Address: 0xfd6d770
                Next-hop reference count: 4
                Source: 172.20.3.23
                Next hop: 172.20.3.23 via ge-0/0/3.21, selected
                Session Id: 0x394
                State: <Active Ext>
                Peer AS:  1021
                Age: 1:34:24
                Validation State: unverified
                Task: BGP_1021.172.20.3.23+179
                Announcement bits (1): 1-KRT
                AS path: 1021 I
                Accepted
                Localpref: 100
                Router ID: 100.64.21.1
                Secondary Tables: inet.0

root@r1> quit
</pre>


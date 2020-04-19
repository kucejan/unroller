#ifndef _DEPARSER_P4_
#define _DEPARSER_P4_

#include <core.p4>

#include "headers.p4"
#include "metadata.p4"

control DeparserImpl(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.unroller_head);
        packet.emit(hdr.unroller_list);
        packet.emit(hdr.ipv4);
    }
}

control computeChecksum(inout headers hdr, inout metadata meta) {
    apply {
        update_checksum(
                hdr.ipv4.isValid(),
                { hdr.ipv4.version, hdr.ipv4.ihl, hdr.ipv4.diffserv,
                hdr.ipv4.totalLen, hdr.ipv4.identification,
                hdr.ipv4.flags, hdr.ipv4.fragOffset, hdr.ipv4.ttl,
                hdr.ipv4.protocol, hdr.ipv4.srcAddr, hdr.ipv4.dstAddr },
                hdr.ipv4.hdrChecksum,
                HashAlgorithm.csum16);
    }
}

#endif /* _DEPARSER_P4_ */

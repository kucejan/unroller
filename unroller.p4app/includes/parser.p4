#ifndef _PARSER_P4_
#define _PARSER_P4_

#include <core.p4>

#include "headers.p4"
#include "metadata.p4"

#define ETHERTYPE_UNRL 16w0x1111
#define ETHERTYPE_IPV4 16w0x0800

parser ParserImpl(packet_in packet, out headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {

    bit<8> unroller_swids;

    @name("parse_ethernet") state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            ETHERTYPE_UNRL: parse_unroller_head;
            ETHERTYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    @name("parse_unroller_head") state parse_unroller_head {
        packet.extract(hdr.unroller_head);
        unroller_swids = hdr.unroller_head.swids;
        transition parse_unroller_list;
    }

    @name("parse_unroller_list") state parse_unroller_list {
        packet.extract(hdr.unroller_list.next);
        unroller_swids = unroller_swids - 1;
        transition select(unroller_swids) {
            0: parse_unroller_next;
            default: parse_unroller_list;
        }
    }

    @name("parse_unroller_next") state parse_unroller_next {
        transition select(hdr.unroller_head.etherType) {
            ETHERTYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    @name("parse_ipv4") state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition accept;
    }

    @name("start") state start {
        transition parse_ethernet;
    }
}

control verifyChecksum(inout headers hdr, inout metadata meta) {
    apply { }
}

#endif /* _PARSER_P4_ */

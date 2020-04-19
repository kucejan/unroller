#ifndef _HEADERS_P4_
#define _HEADERS_P4_

#define UNROLLER_SIZE 1

header ethernet_t {
    bit<48> dstAddr;
    bit<48> srcAddr;
    bit<16> etherType;
}

header ipv4_t {
    bit<4>  version;
    bit<4>  ihl;
    bit<8>  diffserv;
    bit<16> totalLen;
    bit<16> identification;
    bit<3>  flags;
    bit<13> fragOffset;
    bit<8>  ttl;
    bit<8>  protocol;
    bit<16> hdrChecksum;
    bit<32> srcAddr;
    bit<32> dstAddr;
}

header unroller_head_t {
    bit<16> etherType;
    bit<16> hopid;
    bit<8> thcnt;
    bit<8> swids;
}

header unroller_list_t {
    bit<32> swid;
}

struct headers {
    @name("ethernet")
    ethernet_t ethernet;
    @name("unroller_head")
    unroller_head_t unroller_head;
    @name("unroller_list")
    unroller_list_t[UNROLLER_SIZE] unroller_list;
    @name("ipv4")
    ipv4_t ipv4;
}

#endif /* _HEADERS_P4_ */

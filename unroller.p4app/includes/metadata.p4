#ifndef _METADATA_P4_
#define _METADATA_P4_

struct ingress_metadata_t {
    bit<1> drop;
    bit<8> egress_port;
    bit<4> packet_type;
}

struct intrinsic_metadata_t {
    bit<48> ingress_global_timestamp;
    bit<8> lf_field_list;
    bit<16> mcast_grp;
    bit<16> egress_rid;
    bit<8> resubmit_flag;
    bit<8> recirculate_flag;
}

struct queueing_metadata_t {
    bit<48> enq_timestamp;
    bit<16> enq_qdepth;
    bit<32> deq_timedelta;
    bit<16> deq_qdepth;
}

struct metadata {
    @name("ingress_metadata")
    ingress_metadata_t ingress;
    @name("intrinsic_metadata")
    intrinsic_metadata_t intrinsic;
    @name("queueing_metadata")
    queueing_metadata_t queueing;
}

#endif /* _METADATA_P4_ */

#include <core.p4>
#include <v1model.p4>

#include "includes/parser.p4"
#include "includes/deparser.p4"

/*/
|*| UNROLLER digest type
/*/
struct unroller_digest_t {
    bit<48> timestamp;
    bit<32> swid;
    bit<16> hopid;
}

/*/
|*| UNROLLER metadata type
/*/
struct unroller_metadata_t {
    bit<UNROLLER_SIZE> reset;
    bit<UNROLLER_SIZE> match;
    bit<32> swid;
    bit<8> thcnt;
}

/*/
|*| UNROLLER processing control block
/*/
control process_unroller(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {

    // UNROLLER metadata instance
    unroller_metadata_t unroller;

    register<bit<32>>(1) cfg_swid_reg;
    register<bit<8>>(1) cfg_thcnt_reg;

    apply {
        unroller.reset = 0;
        unroller.match = 0;

        // Read switch configuration
        cfg_swid_reg.read(unroller.swid, 0);
        cfg_thcnt_reg.read(unroller.thcnt, 0);

        // Update hop counter
        hdr.unroller_head.hopid = hdr.unroller_head.hopid + 1;

        // Test if we match the identifier
        if (hdr.unroller_list[0].swid == unroller.swid) {
            unroller.match[0:0] = 1w1;
        }

        // Test if we are reseting, if hopid is power of 4
        if (hdr.unroller_head.hopid & (hdr.unroller_head.hopid-1) == 0x0) {
            if ((hdr.unroller_head.hopid & 0xAAAA) == 0x0)
                unroller.reset[0:0] = 1w1;
        }

        // Loop detected?
        if (unroller.match != 0x0) {
            hdr.unroller_head.thcnt = hdr.unroller_head.thcnt + 1;
            if (hdr.unroller_head.thcnt == unroller.thcnt || unroller.thcnt == 0x0) {

                // Inform controller
                digest<unroller_digest_t>(0, {
                    standard_metadata.ingress_global_timestamp,
                    unroller.swid,
                    hdr.unroller_head.hopid
                });

                // Drop packet
                mark_to_drop(standard_metadata);
            }

        // Update packet only
        } else {

            // Update switch identifier, if smaller of we are reseting
            if (unroller.swid < hdr.unroller_list[0].swid || unroller.reset[0:0] == 1) {
                hdr.unroller_list[0].swid = unroller.swid;
            }
        }

    }
}

/*/
|*| Ingress control block
/*/
control ingress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {

    @name("ingress_counter") counter(1, CounterType.packets_and_bytes) ingress_counter;
    @name("process_unroller") process_unroller() process_unroller_0;

    apply {
        ingress_counter.count(0);

        // Forward back to the same port, swap MAC, fill our MAC
        standard_metadata.egress_spec = standard_metadata.ingress_port;
        hdr.ethernet.dstAddr = hdr.ethernet.srcAddr;
        hdr.ethernet.srcAddr = 48w0xAABBCCDDEEFF;

        // Process if UNROLLER header valid
        if (hdr.unroller_head.isValid()) {
            process_unroller_0.apply(hdr, meta, standard_metadata);
        }
    }
}

/*/
|*| Egress control block
/*/
control egress(inout headers hdr, inout metadata meta, inout standard_metadata_t standard_metadata) {
    apply {
    }
}

/*/
|*| Switch package instantiation
/*/
V1Switch(ParserImpl(), verifyChecksum(), ingress(), egress(), computeChecksum(), DeparserImpl()) main;

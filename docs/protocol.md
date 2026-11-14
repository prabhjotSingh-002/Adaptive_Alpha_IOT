# Packet v1 and integration contract

Phase 2 implements explicit unprotected N0, profile 0. Phase 3 adds the separately authenticated AES profile 1; see [Phase 3 security contract](phase3-security-contract.md). Secure runs reject N0 and unknown profiles; this N0 codec is never a receive fallback.

All integers unsigned, big-endian. Header: version u8 (=1), sender u16 (2..configured last node), profile u8 (=0), epoch u16 (=0 in N0), packet counter u32 (starts 1; reject 0), count u8 (1..4). Header = 11 bytes. Each reading: ID u32 (starts 1), creation time u32 milliseconds relative to source boot, value u16. Reading = 10 bytes. Exact packet length 11+10*count; no padding/trailing bytes. Metadata fields are reserved for the master secure envelope; no authentication is claimed. AES/Ascon nonce mapping and AAD verification remain Phase 3+ work.

Decode into temporary bounded state and publish only on full validation. Require increasing IDs inside each batch. Root bounds sender IDs and checks source IPv6 last 16 bits for this fixed Cooja address scheme. This is sanity checking, not identity authentication.

Aggregator capacity 4, configured count cap 1/2/4, byte limit includes reserved overhead, deadline relative to oldest reading. offer rejects wrong source/non-increasing IDs/overflow. build_batch never removes entries. commit_on_send removes only a submitted prefix. Failed route availability retains the queue; expired readings that cannot be submitted are explicitly dropped, avoiding indefinite deadline violation. simple_udp_sendto always returns 0 in this pinned implementation: queue commit means submission to a registered local socket, not radio/root acceptance. No application retry/ack is added.

Root reading dedup uses a 32-ID bounded sliding window per sender; already-seen/too-old IDs are not counted again. This is diagnostic duplicate accounting, not authenticated replay protection. Root receives reordered valid packets inside that window. Payload counters are not used as security state in N0.

Raw events: RSLAB,<node>,<event>,<numeric fields>. Simulator records time_us,node,raw_message; host adds run_id and global sim_time_ms. GEN=id,local_ms,value; TX=counter,count,bytes,oldest_hold_ms,first_id,last_id; RX=sender,counter,id,created_ms,value,duplicate; DROP=id,reason; READY=cap,deadline_ms,period_ms,total; DONE=generated. RX includes auth_ok=false in normalized host events. Sender clock metadata is never subtracted from root local time for latency.

## Phase 3 extension

See [Phase 3 security contract](phase3-security-contract.md) for the protected header, tag, nonce, replay and boot policy. The diagnostic contract above remains applicable to profile 0 only.

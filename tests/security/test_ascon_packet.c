#include "secure_packet.h"
#include "boot_gate.h"
#include "ascon_aead.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
static void grant(void) {
  const uint8_t bytes[4] = {0x42, 0x54, 0x47, 0x31};
  for(unsigned i=0; i<4; ++i) lab_boot_mailbox[i] = bytes[i];
}
int main(void) {
  uint8_t key[16] = {42}, packet[LAB_SECURE_PACKET_MAX], altered[LAB_SECURE_PACKET_MAX];
  lab_security_context tx, rx, wrong;
  lab_security_context aes_tx, aes_rx, ascon_tx, ascon_rx;
  uint8_t aes_key[16] = {11}, ascon_key[16] = {22};
  lab_boot_gate gate;
  lab_batch b = {0}, result, saved;
  size_t len;
  b.sender=2; b.count=1; b.readings[0]=(lab_reading){1,10,20};
  lab_security_init_profile(&tx, LAB_ASCON_PROFILE, 2, 1, key);
  lab_security_init_profile(&rx, LAB_ASCON_PROFILE, 2, 1, key);
  lab_security_init(&wrong, 2, 1, key);
  assert(lab_security_activate(&tx) && lab_security_activate(&rx) && lab_security_activate(&wrong));
  assert(lab_secure_seal(&tx,&b,packet,sizeof packet,&len) && len==37 && packet[3]==2);
  memset(&result,0xa5,sizeof result); saved=result;
  assert(!lab_secure_open(&wrong,packet,len,&result));
  assert(!memcmp(&result,&saved,sizeof result) && !wrong.received.highest);
  memcpy(altered,packet,len); altered[len-1]^=1;
  assert(!lab_secure_open(&rx,altered,len,&result));
  assert(!memcmp(&result,&saved,sizeof result) && !rx.received.highest);
  assert(lab_secure_open(&rx,packet,len,&result) && result.profile==2 && result.readings[0].id==1);
  assert(!lab_secure_open(&rx,packet,len,&result));
  /* Verdicts must preserve output and replay state on every rejection. */
  {
    lab_security_context fresh;
    lab_security_init_profile(&fresh, 2, 2, 1, key);
    assert(lab_secure_open_status(&fresh, packet, len, &result) == LAB_OPEN_LOCKED);
    assert(lab_security_activate(&fresh));
    saved = result;
    assert(lab_secure_open_status(&fresh, packet, 1, &result) == LAB_OPEN_FORMAT);
    memcpy(altered, packet, len); altered[3] = 255;
    assert(lab_secure_open_status(&fresh, altered, len, &result) == LAB_OPEN_PROFILE);
    memcpy(altered, packet, len); altered[5] = 2;
    assert(lab_secure_open_status(&fresh, altered, len, &result) == LAB_OPEN_CONTEXT);
    memcpy(altered, packet, len); altered[len-1] ^= 1;
    assert(lab_secure_open_status(&fresh, altered, len, &result) == LAB_OPEN_AUTH);
    /* Valid tag over a zero reading ID: body validation must fail transactionally. */
    uint8_t nonce[16] = {0x52,0x53,0x4c,2,0,0,2,0,1,0,0,0,1,0,0,0};
    uint8_t body[LAB_READING_BYTES] = {0};
    size_t body_len;
    memcpy(altered, packet, LAB_HEADER);
    assert(lab_ascon_seal(key, nonce, altered, LAB_HEADER, body, sizeof body,
                         altered + LAB_HEADER, sizeof altered - LAB_HEADER, &body_len));
    assert(lab_secure_open_status(&fresh, altered, LAB_HEADER + body_len, &result) == LAB_OPEN_BODY);
    assert(!fresh.received.highest && !memcmp(&result, &saved, sizeof result));
    assert(lab_secure_open_status(&fresh, packet, len, &result) == LAB_OPEN_OK);
    assert(lab_secure_open_status(&fresh, packet, len, &result) == LAB_OPEN_REPLAY);
  }
  lab_security_init_profile(&wrong, 255, 2, 1, key);
  assert(!lab_security_activate(&wrong));
  lab_boot_gate_init_profile(&gate, &wrong, LAB_ASCON_PROFILE, 2, 1, key);
  assert(!wrong.active && !lab_boot_gate_poll(&gate, &wrong));
  lab_boot_mailbox[0] = 0x42;
  assert(!lab_boot_gate_poll(&gate, &wrong));
  grant();
  assert(lab_boot_gate_poll(&gate, &wrong) && wrong.active);
  grant();
  assert(!lab_boot_gate_poll(&gate, &wrong));
  lab_boot_gate_init_profile(&gate, &wrong, 255, 2, 1, key);
  grant();
  assert(!lab_boot_gate_poll(&gate, &wrong) && !wrong.active);
  {
    lab_security_context set[2];
    uint8_t slots[16] = {1,2,0,2,0,1,1,0, 1,2,0,3,0,1,0,0};
    uint8_t zero_keys[32] = {0};
    lab_boot_gate_init_profile(&gate, &set[0], 2, 2, 1, key);
    lab_security_init_profile(&set[1], 2, 3, 1, key);
    grant();
    assert(!lab_boot_gate_poll_set(&gate, set, 2, slots, zero_keys));
    assert(!set[0].active && !set[1].active && gate.consumed);
    slots[14] = 1;
    grant();
    assert(!lab_boot_gate_poll_set(&gate, set, 2, slots, zero_keys));
    lab_boot_gate_init_profile(&gate, &set[0], 2, 2, 1, key);
    lab_security_init_profile(&set[1], 2, 3, 1, key);
    grant();
    assert(lab_boot_gate_poll_set(&gate, set, 2, slots, zero_keys));
    assert(set[0].active && set[1].active);
    assert(!memcmp(set[0].key, zero_keys, 16));
  }
  {
    lab_security_context set[2];
    uint8_t slots[16] = {1,1,0,2,0,1,1,0, 1,2,0,2,0,1,1,0};
    uint8_t keys[32] = {0}; keys[0] = 11; keys[16] = 22;
    lab_boot_gate_init_profile(&gate, &set[0], 1, 2, 1, key);
    lab_security_init_profile(&set[1], 2, 2, 1, key);
    grant();
    assert(lab_boot_gate_poll_set(&gate, set, 2, slots, keys));
    assert(set[0].active && set[1].active && set[0].key[0] == 11 && set[1].key[0] == 22);
    assert(set[0].profile == 1 && set[1].profile == 2);
    lab_boot_gate_init_profile(&gate, &set[0], 1, 2, 1, key);
    lab_security_init_profile(&set[1], 2, 2, 1, key);
    slots[9] = 1; grant();
    assert(!lab_boot_gate_poll_set(&gate, set, 2, slots, keys));
    assert(!set[0].active && !set[1].active && gate.consumed);
  }
  /* Switching profiles must retain independent counters and replay windows. */
  lab_security_init(&aes_tx, 2, 1, aes_key);
  lab_security_init(&aes_rx, 2, 1, aes_key);
  lab_security_init_profile(&ascon_tx, LAB_ASCON_PROFILE, 2, 1, ascon_key);
  lab_security_init_profile(&ascon_rx, LAB_ASCON_PROFILE, 2, 1, ascon_key);
  assert(lab_security_activate(&aes_tx) && lab_security_activate(&aes_rx));
  assert(lab_security_activate(&ascon_tx) && lab_security_activate(&ascon_rx));
  assert(lab_secure_seal(&aes_tx, &b, packet, sizeof packet, &len));
  memcpy(altered, packet, len);
  assert(lab_secure_open(&aes_rx, packet, len, &result));
  assert(lab_secure_seal(&ascon_tx, &b, packet, sizeof packet, &len));
  assert(lab_secure_open(&ascon_rx, packet, len, &result));
  assert(!lab_secure_open(&aes_rx, altered, len, &result));
  assert(lab_secure_seal(&aes_tx, &b, packet, sizeof packet, &len));
  assert(aes_tx.next_counter == 3 && ascon_tx.next_counter == 2);
  assert(lab_secure_open(&aes_rx, packet, len, &result));
  assert(aes_rx.received.highest == 2 && ascon_rx.received.highest == 1);
  puts("Ascon secure packet dispatch, isolation and replay: PASS");
  return 0;
}

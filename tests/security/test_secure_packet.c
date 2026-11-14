#include "secure_packet.h"
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
int main(void) {
  uint8_t key[16] = {1}, packet[LAB_SECURE_PACKET_MAX], forged[LAB_SECURE_PACKET_MAX];
  size_t len;
  lab_security_context tx, rx;
  lab_batch batch = {0}, result, sentinel;
  batch.sender = 2; batch.count = 2; batch.readings[0] = (lab_reading){1, 10, 20};
  batch.readings[1] = (lab_reading){2, 20, 30};
  lab_security_init(&tx, 2, 1, key); lab_security_init(&rx, 2, 1, key);
  assert(!lab_secure_seal(&tx, &batch, packet, sizeof packet, &len));
  assert(lab_security_activate(&tx) && lab_security_activate(&rx));
  assert(lab_secure_seal(&tx, &batch, packet, sizeof packet, &len) && len == 47);
  memcpy(forged, packet, len); forged[6] = 0x7f;
  memset(&result, 0xa5, sizeof result); sentinel = result;
  assert(!lab_secure_open(&rx, forged, len, &result));
  assert(!memcmp(&result, &sentinel, sizeof result) && !rx.received.highest);
  memset(&result, 0xa5, sizeof result); sentinel = result;
  assert(!lab_secure_open(&rx, packet, len - 1, &result));
  assert(!memcmp(&result, &sentinel, sizeof result) && !rx.received.highest);
  memcpy(forged, packet, len); forged[3] = 0;
  assert(!lab_secure_open(&rx, forged, len, &result));
  memcpy(forged, packet, len); forged[3] = 255;
  assert(!lab_secure_open(&rx, forged, len, &result));
  assert(lab_secure_open(&rx, packet, len, &result));
  assert(result.profile == 1 && result.epoch == 1 && result.readings[1].id == 2);
  assert(!lab_secure_open(&rx, packet, len, &result));
  assert(lab_secure_seal(&tx, &batch, packet, sizeof packet, &len));
  packet[len-1] ^= 1; assert(!lab_secure_open(&rx, packet, len, &result));
  packet[len-1] ^= 1; assert(lab_secure_open(&rx, packet, len, &result));
  lab_security_lock(&tx); assert(!lab_security_activate(&tx));
  assert(!lab_secure_seal(&tx, &batch, packet, sizeof packet, &len));
  lab_security_init(&tx, 2, 1, key); assert(!tx.active);
  /* Reordering is permitted within the 32-counter packet window. */
  lab_security_context tx2, rx2;
  uint8_t packets[33][LAB_SECURE_PACKET_MAX];
  size_t lengths[33];
  lab_security_init(&tx2, 2, 1, key); lab_security_init(&rx2, 2, 1, key);
  assert(lab_security_activate(&tx2) && lab_security_activate(&rx2));
  for(unsigned i = 0; i < 33; i++)
    assert(lab_secure_seal(&tx2, &batch, packets[i], sizeof packets[i], &lengths[i]));
  assert(lab_secure_open(&rx2, packets[32], lengths[32], &result));
  assert(lab_secure_open(&rx2, packets[1], lengths[1], &result)); /* delta 31 */
  assert(!lab_secure_open(&rx2, packets[0], lengths[0], &result)); /* delta 32 */
  assert(!lab_secure_open(&rx2, packets[1], lengths[1], &result));
  tx2.next_counter = UINT32_MAX - 1;
  assert(lab_secure_seal(&tx2, &batch, packet, sizeof packet, &len));
  assert(tx2.next_counter == UINT32_MAX);
  assert(!lab_secure_seal(&tx2, &batch, packet, sizeof packet, &len));
  uint8_t a[13], b[13];
  assert(lab_security_nonce(2, 1, 1, a) && lab_security_nonce(3, 1, 1, b));
  assert(memcmp(a, b, sizeof a));
  assert(!lab_security_nonce(2, 1, UINT32_MAX, a));
  /* A valid tag over an invalid reading must not advance replay state. */
  lab_security_context tx3, rx3;
  uint8_t malformed[LAB_SECURE_PACKET_MAX], body[LAB_READING_BYTES] = {0}, nonce[13];
  size_t protected_len;
  lab_security_init(&tx3, 2, 1, key); lab_security_init(&rx3, 2, 1, key);
  assert(lab_security_activate(&tx3) && lab_security_activate(&rx3));
  batch.count = 1;
  assert(lab_secure_seal(&tx3, &batch, packet, sizeof packet, &len));
  memcpy(malformed, packet, LAB_HEADER);
  assert(lab_security_nonce(2, 1, 1, nonce));
  assert(lab_ccm_seal(key, nonce, malformed, LAB_HEADER, body, sizeof body,
                      malformed + LAB_HEADER, sizeof malformed - LAB_HEADER, &protected_len));
  assert(!lab_secure_open(&rx3, malformed, LAB_HEADER + protected_len, &result));
  assert(rx3.received.highest == 0);
  assert(lab_secure_open(&rx3, packet, len, &result));
  puts("Secure packet authentication, replay and lock checks passed");
  return 0;
}

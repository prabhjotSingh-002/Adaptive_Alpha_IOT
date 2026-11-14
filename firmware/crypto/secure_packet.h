#ifndef LAB_SECURE_PACKET_H
#define LAB_SECURE_PACKET_H
#include "protocol.h"
#include "aes_ccm.h"
#define LAB_SECURE_PROFILE 1u
#define LAB_ASCON_PROFILE 2u
#define LAB_SECURE_PACKET_MAX (LAB_PACKET_MAX + LAB_CCM_TAG_SIZE)
typedef struct {
  uint8_t key[LAB_CCM_KEY_SIZE];
  uint16_t sender, epoch;
  uint8_t profile;
  uint32_t next_counter;
  lab_seen received;
  bool active;
} lab_security_context;
/* Initialization always starts locked. Authorize only through a validated
 * one-use provisioning mechanism; this API does not establish one itself. */
void lab_security_init(lab_security_context *ctx, uint16_t sender, uint16_t epoch,
                       const uint8_t key[LAB_CCM_KEY_SIZE]);
void lab_security_init_profile(lab_security_context *ctx, uint8_t profile,
                               uint16_t sender, uint16_t epoch, const uint8_t key[16]);
bool lab_security_activate(lab_security_context *ctx);
void lab_security_lock(lab_security_context *ctx);
bool lab_security_nonce(uint16_t sender, uint16_t epoch, uint32_t counter,
                        uint8_t nonce[LAB_CCM_NONCE_SIZE]);
/* Counter is consumed before encryption. On failure out_len is zero. */
bool lab_secure_seal(lab_security_context *ctx, const lab_batch *batch,
                     uint8_t *out, size_t capacity, size_t *out_len);
typedef enum {
  LAB_OPEN_OK = 0, LAB_OPEN_FORMAT, LAB_OPEN_PROFILE, LAB_OPEN_CONTEXT,
  LAB_OPEN_LOCKED, LAB_OPEN_REPLAY, LAB_OPEN_AUTH, LAB_OPEN_BODY
} lab_open_status;
/* No caller output or replay mutation on rejection. Status metadata is not
 * proof that rejected header fields were authenticated. */
lab_open_status lab_secure_open_status(lab_security_context *ctx,
                                      const uint8_t *packet, size_t length,
                                      lab_batch *out);
/* Compatibility wrapper: true only for LAB_OPEN_OK. */
bool lab_secure_open(lab_security_context *ctx, const uint8_t *packet,
                     size_t length, lab_batch *out);
#endif

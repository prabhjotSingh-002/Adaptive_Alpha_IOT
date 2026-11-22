#ifndef LAB_SECURE_PACKET_H
#define LAB_SECURE_PACKET_H
#include "protocol.h"

#define LAB_SECURE_PROFILE 1u
#define LAB_ASCON_PROFILE 2u
#define LAB_SPECK_PROFILE 3u
#define LAB_PRESENT_PROFILE 4u

#define LAB_CCM_KEY_SIZE 16u
#define LAB_CCM_NONCE_SIZE 13u
#define LAB_CCM_TAG_SIZE 16u

#define LAB_SECURE_PACKET_MAX (LAB_PACKET_MAX + LAB_CCM_TAG_SIZE)

typedef struct {
  uint8_t key[LAB_CCM_KEY_SIZE];
  uint16_t sender, epoch;
  uint8_t profile;
  uint32_t next_counter;
  lab_seen received;
  bool active;
} lab_security_context;

void lab_security_init(lab_security_context *ctx, uint16_t sender, uint16_t epoch,
                       const uint8_t key[LAB_CCM_KEY_SIZE]);
void lab_security_init_profile(lab_security_context *ctx, uint8_t profile,
                               uint16_t sender, uint16_t epoch, const uint8_t key[16]);
bool lab_security_activate(lab_security_context *ctx);
void lab_security_lock(lab_security_context *ctx);
bool lab_security_nonce(uint16_t sender, uint16_t epoch, uint32_t counter,
                        uint8_t nonce[LAB_CCM_NONCE_SIZE]);
bool lab_secure_seal(lab_security_context *ctx, const lab_batch *batch,
                     uint8_t *out, size_t capacity, size_t *out_len);

typedef enum {
  LAB_OPEN_OK = 0, LAB_OPEN_FORMAT, LAB_OPEN_PROFILE, LAB_OPEN_CONTEXT,
  LAB_OPEN_LOCKED, LAB_OPEN_REPLAY, LAB_OPEN_AUTH, LAB_OPEN_BODY
} lab_open_status;

lab_open_status lab_secure_open_status(lab_security_context *ctx,
                                      const uint8_t *packet, size_t length,
                                      lab_batch *out);
bool lab_secure_open(lab_security_context *ctx, const uint8_t *packet,
                     size_t length, lab_batch *out);
#endif

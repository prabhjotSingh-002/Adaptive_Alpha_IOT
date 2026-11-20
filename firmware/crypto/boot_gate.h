#ifndef LAB_BOOT_GATE_H
#define LAB_BOOT_GATE_H
#include "secure_packet.h"
#define LAB_BOOT_MAILBOX_SIZE 4u
/* Visible to the simulator. It must start at zero and is consumed before use. */
extern volatile uint8_t lab_boot_mailbox[LAB_BOOT_MAILBOX_SIZE];
bool lab_boot_grant_pending(void);
typedef struct { bool consumed; } lab_boot_gate;
void lab_boot_gate_init(lab_boot_gate *gate, lab_security_context *ctx,
                        uint16_t sender, uint16_t epoch, const uint8_t key[16]);
void lab_boot_gate_init_profile(lab_boot_gate *gate, lab_security_context *ctx,
                                uint8_t profile, uint16_t sender, uint16_t epoch,
                                const uint8_t key[16]);
bool lab_boot_gate_poll(lab_boot_gate *gate, lab_security_context *ctx);
/* Metadata per slot: version, profile, sender BE16, epoch BE16, ready, reserved.
 * Slots and keys are contiguous and must match the preinitialized contexts. */
#define LAB_PROVISION_SLOT_SIZE 8u
#define LAB_PROVISION_MAX_CONTEXTS 30u
bool lab_boot_gate_poll_set(lab_boot_gate *gate, lab_security_context *contexts,
                            size_t count, const uint8_t *metadata,
                            const uint8_t *keys);
#endif

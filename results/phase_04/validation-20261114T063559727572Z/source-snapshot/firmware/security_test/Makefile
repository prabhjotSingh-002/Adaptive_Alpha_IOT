CONTIKI_PROJECT = crypto_kat boot_kat reset_kat ascon_kat
CONTIKI = ../../external/contiki-ng
PROJECTDIRS += ../crypto ../common
PROJECT_SOURCEFILES += aes_ccm.c secure_packet.c boot_gate.c protocol.c
CFLAGS += -I../crypto -I../common
include ../crypto/aes-backend.mk
include ../crypto/ascon-backend.mk
all: $(CONTIKI_PROJECT)
include $(CONTIKI)/Makefile.include

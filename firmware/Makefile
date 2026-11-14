CONTIKI = ../../external/contiki-ng
PROJECTDIRS += ../common ../aggregate ../crypto ../energy ../policy
PROJECT_SOURCEFILES += protocol.c aggregate.c aes_ccm.c secure_packet.c boot_gate.c energy.c energest_sampler.c policy.c
include ../crypto/aes-backend.mk
include ../crypto/ascon-backend.mk
CFLAGS += -I..
include $(CONTIKI)/Makefile.include

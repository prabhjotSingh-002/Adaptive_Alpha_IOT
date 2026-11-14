# Shared application and mote-test backend selection.
ASCON_DIR = ../../external/ascon-c
ASCON_IMPL ?= ref
ifneq ($(filter $(ASCON_IMPL),ref opt32_lowsize),$(ASCON_IMPL))
$(error Unsupported ASCON_IMPL)
endif
ASCON_BACKEND = $(ASCON_DIR)/crypto_aead/asconaead128/$(ASCON_IMPL)
PROJECTDIRS += $(ASCON_BACKEND)
PROJECT_SOURCEFILES += ascon_aead.c aead.c
ifeq ($(ASCON_IMPL),opt32_lowsize)
PROJECT_SOURCEFILES += crypto_aead.c permutations.c update.c
endif
CFLAGS += -DLAB_ENABLE_ASCON -I$(ASCON_DIR)/tests -I$(ASCON_BACKEND)

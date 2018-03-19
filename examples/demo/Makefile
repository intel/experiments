TEMP_FILE:=$(shell mktemp)
GCR_PROJECT := $(shell gcloud config get-value project 2> /dev/null)
VERSION := $(shell git describe --tags --always --dirty)
IMG := "gcr.io/$(GCR_PROJECT)/experiments:$(VERSION)"
UID := $(shell uuidgen|tr [:upper:] [:lower:]|tail -c 8)
CRD_NAME := "test-$(UID)"

submit:
	cp experiment-test.yaml $(TEMP_FILE)
	sed -i -e 's#{{img}}#$(IMG)#g' $(TEMP_FILE)
	sed -i -e 's#{{crd_name}}#$(CRD_NAME)#g' $(TEMP_FILE)
	kubectl create -f $(TEMP_FILE)
	rm $(TEMP_FILE)

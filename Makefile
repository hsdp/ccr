OUTDIR = ./build

.PHONY: centos7 centos6 alpine37 alpine310 debian9 debian10 ubuntu14 ubuntu16 clean all list

all: alpine37 alpine310 centos7 centos6 debian9 debian10 ubuntu14 ubuntu16

list:
	@$(MAKE) -rpn | sed -n -e '/^$$/ { n ; /^[^ .#][^ ]*:/ { s/:.*$$// ; p ; } ; }' | sort

alpine37 alpine310 centos6 centos7 debian9 debian10 ubuntu14 ubuntu16:
	@if [ ! -d $(OUTDIR) ]; then mkdir -p $(OUTDIR); fi
	@echo "Symlinking $@ Dockerfile.."
	@ln -s $@/Dockerfile ./Dockerfile
	@echo "Building docker image..."
	@docker build . -t $@-ccr
	@echo "Exporting image to build/$@-ccr.tar"
	@docker save --output build/$@-ccr.tar $@-ccr
	@echo "Cleaning up."
	@rm ./Dockerfile
	@echo "Done."

clean:
	@echo "Removing previous build.."
	@if [ -L ./Dockerfile ]; then rm -f ./Dockerfile; fi
	@rm -f build/*
	@echo "Done."

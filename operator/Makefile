# SPDX-FileCopyrightText: the secureCodeBox authors
#
# SPDX-License-Identifier: Apache-2.0

include ../prerequisites.mk
include ../env-paths.mk
## Telling the env-paths file where the root project dir is. This is done to allow the generation of the paths of the different project folders relative to where the makefile is being run from.
## So BIN_DIR= $(PROJECT_DIR)/bin will be BIN_DIR=../bin
PROJECT_DIR=..

IMG_NS ?= securecodebox

# ENVTEST_K8S_VERSION refers to the version of kubebuilder assets to be downloaded by envtest binary.
ENVTEST_K8S_VERSION = 1.33.0

# Image URL to use all building/pushing image targets for the operator
OPERATOR_IMG ?= operator

# Image URL to use all building/pushing image targets for the lurker
LURKER_IMG ?= lurker

# Tag used for the images
IMG_TAG ?= sha-$$(git rev-parse --short HEAD)

# Get the currently used golang install path (in GOPATH/bin, unless GOBIN is set)
# IMPORTANT: The body of conditionals MUST not be indented! Indentation result in
# errors on macOS/FreeBSD because the line wil be interpreted as command which must
# inside a recipe (target). (see https://github.com/secureCodeBox/secureCodeBox/issues/1353)
ifeq (,$(shell go env GOBIN))
GOBIN=$(shell go env GOPATH)/bin
else
GOBIN=$(shell go env GOBIN)
endif

# Setting SHELL to bash allows bash commands to be executed by recipes.
# This is a requirement for 'setup-envtest.sh' in the test target.
# Options are set to exit when a recipe line exits non-zero or a piped command fails.
SHELL = /usr/bin/env bash -o pipefail
.SHELLFLAGS = -ec

all: build

##@ General

# The help target prints out all targets with their descriptions organized
# beneath their categories. The categories are represented by '##@' and the
# target descriptions by '##'. The awk commands is responsible for reading the
# entire set of makefiles included in this invocation, looking for lines of the
# file as xyz: ## something, and then pretty-format the target and help. Then,
# if there's a line with ##@ something, that gets pretty-printed as a category.
# More info on the usage of ANSI control characters for terminal formatting:
# https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_parameters
# More info on the awk command:
# http://linuxcommand.org/lc3_adv_awk.php

.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

.PHONY: manifests
manifests: controller-gen ## Generate WebhookConfiguration, ClusterRole and CustomResourceDefinition objects.
	$(CONTROLLER_GEN) rbac:roleName="securecodebox-manager-role",headerFile="hack/boilerplate.yaml.txt" crd:maxDescLen=256,headerFile="hack/boilerplate.yaml.txt" webhook paths="./..." output:crd:artifacts:config=crds output:rbac:artifacts:config=templates/rbac

.PHONY: generate
generate: controller-gen ## Generate code containing DeepCopy, DeepCopyInto, and DeepCopyObject method implementations.
	$(CONTROLLER_GEN) object:headerFile="hack/boilerplate.go.txt" paths="./..."

.PHONY: fmt
fmt: ## Run go fmt against code.
	go fmt ./...

.PHONY: vet
vet: ## Run go vet against code.
	go vet ./...

.PHONY: test
test: manifests generate fmt vet envtest ## Run tests.
	KUBEBUILDER_ASSETS="$(shell $(ENVTEST) use $(ENVTEST_K8S_VERSION) --bin-dir $(LOCALBIN) -p path)" go test -tags="fast slow" ./... -coverprofile cover.out

.PHONY: test-fast
test-fast: manifests generate fmt vet envtest ## Run tests.
	KUBEBUILDER_ASSETS="$(shell $(ENVTEST) use $(ENVTEST_K8S_VERSION) -p path)" go test -tags="fast" ./... -coverprofile cover.out

.PHONY: view-coverage
view-coverage:
	go tool cover -html=cover.out

## Helm unit tests
.PHONY: helm-unit-tests
helm-unit-tests:
	echo "Running helm unit tests for operator"; \
	helm unittest . \

##@ Build

.PHONY: build
build: generate fmt vet ## Build manager binary.
	go build -o bin/manager main.go

.PHONY: run
run: manifests generate fmt vet ## Run a controller from your host.
	go run ./main.go

.PHONY: docker-build
docker-build: ## Build docker image with the manager.
	@echo ".: ⚙️ Build Container Images"
	docker build -t $(IMG_NS)/${OPERATOR_IMG}:${IMG_TAG} .
	cd $(PROJECT_DIR)/lurker && docker build -t $(IMG_NS)/$(LURKER_IMG):$(IMG_TAG) .

.PHONY: docker-push
docker-push: ## Push docker image with the manager.
	docker push $(IMG_NS)/${OPERATOR_IMG}:${IMG_TAG}
	docker push $(IMG_NS)/$(LURKER_IMG):$(IMG_TAG)

.PHONY: docker-export
docker-export:
	$(MAKE) docker-export-operator
	$(MAKE) docker-export-lurker

.PHONY: docker-export-operator
docker-export-operator:
	@echo ".: 💾 Export Operator Image"
	docker save $(IMG_NS)/$(OPERATOR_IMG):$(IMG_TAG) > $(OPERATOR_IMG).tar

.PHONY: docker-export-lurker
docker-export-lurker:
	@echo ".: 💾 Export Lurker Image"
	docker save $(IMG_NS)/$(LURKER_IMG):$(IMG_TAG) > $(LURKER_IMG).tar

##@ Deployment

.PHONY: kind-import
kind-import:
	@echo ".: 💾 Importing the image archive to local kind cluster."
	kind load image-archive ./$(OPERATOR_IMG).tar
	kind load image-archive ./$(LURKER_IMG).tar

.PHONY: helm-deploy
helm-deploy:
	@echo ".: ⚙️ Deploying Operator with the Image tag '$(IMG_TAG)' into kind."
	# If not exists create namespace where the tests will be executed
	kubectl create namespace integration-tests --dry-run=client -o yaml | kubectl apply -f -
	# If not exists create secureCodeBox operator namespace
	kubectl create namespace securecodebox-system --dry-run=client -o yaml | kubectl apply -f -

	MINIO_ROOT_USER=$(kubectl get secret securecodebox-operator-minio -n securecodebox-system -o=jsonpath='{.data.root-user}' | base64 --decode)
	MINIO_ROOT_PASSWORD=$(kubectl get secret --namespace "securecodebox-system" securecodebox-operator-minio -o jsonpath="{.data.root-password}" | base64 -d)

	helm -n securecodebox-system upgrade --install securecodebox-operator ./ --wait \
		--set="image.repository=docker.io/$(IMG_NS)/$(OPERATOR_IMG)" \
		--set="image.tag=$(IMG_TAG)" \
		--set="image.pullPolicy=IfNotPresent" \
		--set="lurker.image.repository=docker.io/$(IMG_NS)/$(LURKER_IMG)" \
		--set="lurker.image.tag=$(IMG_TAG)" \
		--set="lurker.image.pullPolicy=IfNotPresent" \
		--set="minio.auth.rootUser = $(MINIO_ROOT_USER)" \
		--set="minio.auth.rootPassword = $(MINIO_ROOT_PASSWORD)"

.PHONY: install
install: manifests ## Install CRDs into the K8s cluster specified in ~/.kube/config.
	kubectl apply -f ./crds/

.PHONY: uninstall
uninstall: manifests ## Uninstall CRDs from the K8s cluster specified in ~/.kube/config.
	kubectl delete -f ./crds/

##@ Build Dependencies

## Location to install dependencies to
LOCALBIN ?= $(shell pwd)/bin
$(LOCALBIN):
	mkdir -p $(LOCALBIN)

## Tool Binaries
CONTROLLER_GEN ?= $(LOCALBIN)/controller-gen-$(CONTROLLER_TOOLS_VERSION)
ENVTEST ?= $(LOCALBIN)/setup-envtest-$(ENVTEST_VERSION)

## Tool Versions
CONTROLLER_TOOLS_VERSION ?= v0.18.0
ENVTEST_VERSION ?= release-0.21

.PHONY: controller-gen
controller-gen: $(CONTROLLER_GEN) ## Download controller-gen locally if necessary.
$(CONTROLLER_GEN): $(LOCALBIN)
	$(call go-install-tool,$(CONTROLLER_GEN),sigs.k8s.io/controller-tools/cmd/controller-gen,$(CONTROLLER_TOOLS_VERSION))

.PHONY: envtest
envtest: $(ENVTEST) ## Download setup-envtest locally if necessary.
$(ENVTEST): $(LOCALBIN)
	$(call go-install-tool,$(ENVTEST),sigs.k8s.io/controller-runtime/tools/setup-envtest,$(ENVTEST_VERSION))

# go-install-tool will 'go install' any package with custom target and name of binary, if it doesn't exist
# $1 - target path with name of binary (ideally with version)
# $2 - package url which can be installed
# $3 - specific version of package
define go-install-tool
@[ -f $(1) ] || { \
set -e; \
package=$(2)@$(3) ;\
echo "Downloading $${package}" ;\
GOBIN=$(LOCALBIN) go install $${package} ;\
mv "$$(echo "$(1)" | sed "s/-$(3)$$//")" $(1) ;\
}
endef

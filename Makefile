SHELL := /bin/zsh
ROOT_DIR := $(abspath .)
VENV_DIR := $(ROOT_DIR)/.venv
PYTHON := $(VENV_DIR)/bin/python
STAMP := $(VENV_DIR)/.bootstrap-complete

.DEFAULT_GOAL := help

.PHONY: help install smoke test stdio mcpb list-tools list-resources list-adapters read-core-primer invoke-example

help:
	@echo "dcn-mcp targets:"
	@echo "  make install        Create/update the local .venv and install dcn-mcp"
	@echo "  make smoke          Run the repo smoke test"
	@echo "  make test           Run the full test suite"
	@echo "  make stdio          Run the real MCP stdio server"
	@echo "  make mcpb           Build a Claude Desktop .mcpb bundle in dist/"
	@echo "  make list-tools     List local tool metadata"
	@echo "  make list-resources List local resource metadata"
	@echo "  make list-adapters  List registered adapters"
	@echo "  make read-core-primer Read the core primer resource"
	@echo "  make invoke-example Run a sample local tool invocation"

$(STAMP): pyproject.toml scripts/bootstrap_venv.sh
	./scripts/bootstrap_venv.sh
	@touch $(STAMP)

install: $(STAMP)
	@echo "dcn-mcp is installed in $(VENV_DIR)"

smoke: $(STAMP)
	./scripts/smoke_test.sh

test: $(STAMP)
	source $(VENV_DIR)/bin/activate && python -m unittest discover -s tests -v

stdio: $(STAMP)
	./scripts/run_stdio.sh

mcpb: $(STAMP)
	./scripts/build_mcpb.sh

list-tools: $(STAMP)
	source $(VENV_DIR)/bin/activate && python -m dcn_mcp.server list-tools

list-resources: $(STAMP)
	source $(VENV_DIR)/bin/activate && python -m dcn_mcp.server list-resources

list-adapters: $(STAMP)
	source $(VENV_DIR)/bin/activate && python -m dcn_mcp.server list-adapters

read-core-primer: $(STAMP)
	source $(VENV_DIR)/bin/activate && python -m dcn_mcp.server read-resource core.dcn_core_primer

invoke-example: $(STAMP)
	source $(VENV_DIR)/bin/activate && python -m dcn_mcp.server invoke core.build_parent_connector '{"name":"piece","child_names":["a","b"]}'

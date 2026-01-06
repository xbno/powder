.PHONY: venv clean install update test test-unit test-all rebuild help run

# Define Python from venv
PYTHON := .venv/bin/python
# Define UV_EXECUTABLE as the system-wide uv command (not from venv)
UV_EXECUTABLE := $(shell which uv 2>/dev/null || echo "uv")

# Default target - complete setup
all: venv install
	@echo ""
	@echo "Setup complete!"
	@echo "Virtual environment created"
	@echo "Dependencies installed"
	@echo ""
	@echo "Ready to use! Try:"
	@echo "  make test         - Run tests"
	@echo "  make run          - Run the agent"

# Create virtual environment
venv:
ifndef UV_EXECUTABLE
	$(error "uv command not found in your system PATH. Please install uv or ensure it's in your PATH.")
endif
	@echo "Creating virtual environment using $(UV_EXECUTABLE)..."
	$(UV_EXECUTABLE) venv .venv
	@echo "Virtual environment .venv created."

# Install dependencies
install: venv
ifndef UV_EXECUTABLE
	$(error "uv command not found. Run 'make venv' or ensure uv is in PATH.")
endif
ifeq ($(wildcard $(PYTHON)),)
	$(error "$(PYTHON) not found. Run 'make venv' first to create the virtual environment.")
endif
	@echo "Installing dependencies into $(PYTHON) using $(UV_EXECUTABLE)..."
	$(UV_EXECUTABLE) pip install -r requirements.txt --python $(PYTHON)

# Update dependencies (compile requirements.in -> requirements.txt)
update:
ifndef UV_EXECUTABLE
	$(error "uv command not found. Run 'make venv' or ensure uv is in PATH.")
endif
ifeq ($(wildcard $(PYTHON)),)
	$(error "$(PYTHON) not found. Run 'make venv' first to create the virtual environment.")
endif
	@echo "Updating requirements.txt using $(UV_EXECUTABLE) for $(PYTHON)..."
	$(UV_EXECUTABLE) pip compile requirements.in -o requirements.txt --python $(PYTHON)
	@echo "Installing updated dependencies into $(PYTHON) using $(UV_EXECUTABLE)..."
	$(UV_EXECUTABLE) pip install -r requirements.txt --python $(PYTHON)

# Clean virtual environment
clean:
	@echo "Cleaning virtual environment..."
	rm -rf .venv
	rm -rf __pycache__
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Rebuild virtual environment
rebuild: clean venv install

# Default test command
test: test-unit

# Run unit tests
test-unit:
ifeq ($(wildcard $(PYTHON)),)
	$(error "$(PYTHON) not found. Run 'make venv' first.")
endif
	@echo "Running unit tests..."
	$(PYTHON) -m pytest tests/ -v

# Run all tests with coverage
test-all:
ifeq ($(wildcard $(PYTHON)),)
	$(error "$(PYTHON) not found. Run 'make venv' first.")
endif
	@echo "Running all tests with coverage..."
	$(PYTHON) -m pytest tests/ -v --cov=powder

# Run the agent (interactive)
run:
ifeq ($(wildcard $(PYTHON)),)
	$(error "$(PYTHON) not found. Run 'make venv' first.")
endif
	$(PYTHON) -m powder.agent

# Run evaluation
eval:
ifeq ($(wildcard $(PYTHON)),)
	$(error "$(PYTHON) not found. Run 'make venv' first.")
endif
	$(PYTHON) -m powder.eval.backtest

# Seed the database
seed-db:
ifeq ($(wildcard $(PYTHON)),)
	$(error "$(PYTHON) not found. Run 'make venv' first.")
endif
	$(PYTHON) -m powder.data.seed_mountains

# Help command
help:
	@echo "Available commands:"
	@echo "  make              - Setup virtual environment and install dependencies"
	@echo "  make venv         - Create virtual environment"
	@echo "  make install      - Install dependencies"
	@echo "  make update       - Update dependencies (compile requirements.in)"
	@echo "  make clean        - Remove virtual environment"
	@echo "  make rebuild      - Rebuild virtual environment"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run unit tests"
	@echo "  make test-all     - Run all tests with coverage"
	@echo ""
	@echo "Running:"
	@echo "  make run          - Run the agent interactively"
	@echo "  make eval         - Run evaluation/backtesting"
	@echo "  make seed-db      - Seed the mountain database"

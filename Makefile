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

# Default test command (excludes LLM tests)
test: test-fast

# Run fast tests (no LLM calls)
test-fast:
ifeq ($(wildcard $(PYTHON)),)
	$(error "$(PYTHON) not found. Run 'make venv' first.")
endif
	@echo "Running fast tests (no LLM)..."
	$(PYTHON) -m pytest tests/ -v -m "not llm"

# Run LLM tests only (requires ANTHROPIC_API_KEY)
test-llm:
ifeq ($(wildcard $(PYTHON)),)
	$(error "$(PYTHON) not found. Run 'make venv' first.")
endif
	@echo "Running LLM tests..."
	$(PYTHON) -m pytest tests/ -v -m "llm"

# Run all tests
test-all:
ifeq ($(wildcard $(PYTHON)),)
	$(error "$(PYTHON) not found. Run 'make venv' first.")
endif
	@echo "Running all tests..."
	$(PYTHON) -m pytest tests/ -v

# Run all tests with coverage
test-cov:
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
	$(PYTHON) -m powder.evals.runner

# Run evaluation with verbose output
eval-verbose:
ifeq ($(wildcard $(PYTHON)),)
	$(error "$(PYTHON) not found. Run 'make venv' first.")
endif
	$(PYTHON) -m powder.evals.runner --verbose

# Fetch historic weather data for backtesting
fetch-historic:
ifeq ($(wildcard $(PYTHON)),)
	$(error "$(PYTHON) not found. Run 'make venv' first.")
endif
	@echo "Fetching historic weather data (takes ~2 minutes)..."
	$(PYTHON) -m powder.evals.fetch_historic

# Show available backtest scenarios
backtest-summary:
ifeq ($(wildcard $(PYTHON)),)
	$(error "$(PYTHON) not found. Run 'make venv' first.")
endif
	$(PYTHON) -m powder.evals.fetch_historic --summary

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
	@echo "  make test         - Run fast tests (no LLM calls)"
	@echo "  make test-fast    - Run fast tests (no LLM calls)"
	@echo "  make test-llm     - Run LLM tests only (requires ANTHROPIC_API_KEY)"
	@echo "  make test-all     - Run all tests"
	@echo "  make test-cov     - Run all tests with coverage"
	@echo ""
	@echo "Running:"
	@echo "  make run            - Run the agent interactively"
	@echo "  make eval           - Run evaluation suite"
	@echo "  make eval-verbose   - Run evaluation with detailed output"
	@echo "  make fetch-historic - Fetch historic weather for backtesting"
	@echo "  make backtest-summary - Show available backtest scenarios"
	@echo "  make seed-db        - Seed the mountain database"

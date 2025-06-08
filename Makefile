# CodeWeave Makefile
# Provides easy installation and management commands

.PHONY: help install install-dev uninstall clean test global-script install-global uninstall-global

# Default target
help:
	@echo "CodeWeave - Intelligent source code aggregation and AI workflow optimization"
	@echo ""
	@echo "Available commands:"
	@echo "  make install        - Install CodeWeave package"
	@echo "  make install-dev    - Install in development mode"
	@echo "  make install-global - Install package + global script (requires sudo)"
	@echo "  make global-script  - Install global script only (requires sudo)"
	@echo "  make uninstall      - Uninstall CodeWeave package"
	@echo "  make uninstall-global - Remove global script (requires sudo)"
	@echo "  make test          - Run test suite"
	@echo "  make clean         - Remove build artifacts"
	@echo "  make help          - Show this help message"
	@echo ""
	@echo "After installation, you can use:"
	@echo "  codeweave <path>           # Using global script"
	@echo "  python -m codeweave <path> # Using Python module"
	@echo "  cw <path>                  # Short alias"

# Install the package
install:
	@echo "Installing CodeWeave..."
	pip install .
	@echo "✓ CodeWeave installed successfully!"
	@echo "Usage: python -m codeweave <path> or codeweave <path>"

# Install in development mode
install-dev:
	@echo "Installing CodeWeave in development mode..."
	pip install -e .
	@echo "✓ CodeWeave installed in development mode!"

# Install package and global script
install-global: install global-script
	@echo "✓ CodeWeave installed with global script access!"
	@echo "You can now use 'codeweave' from anywhere."

# Install the global script to /usr/local/bin
global-script:
	@echo "Installing global CodeWeave script..."
	@if [ ! -d "/usr/local/bin" ]; then \
		echo "Creating /usr/local/bin directory..."; \
		sudo mkdir -p /usr/local/bin; \
	fi
	sudo cp scripts/codeweave /usr/local/bin/codeweave
	sudo chmod +x /usr/local/bin/codeweave
	@echo "✓ Global script installed to /usr/local/bin/codeweave"

# Uninstall the package
uninstall:
	@echo "Uninstalling CodeWeave..."
	pip uninstall codeweave -y
	@echo "✓ CodeWeave uninstalled"

# Remove global script
uninstall-global:
	@echo "Removing global CodeWeave script..."
	@if [ -f "/usr/local/bin/codeweave" ]; then \
		sudo rm /usr/local/bin/codeweave; \
		echo "✓ Global script removed"; \
	else \
		echo "Global script not found"; \
	fi

# Run tests
test:
	@echo "Running CodeWeave tests..."
	python -m pytest test/ -v

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✓ Build artifacts cleaned"

# Quick development setup
dev: clean install-dev
	@echo "✓ Development environment ready!"

# Complete setup (install + global script)
setup: clean install-global
	@echo "✓ Complete CodeWeave setup finished!"
	@echo ""
	@echo "Try it out:"
	@echo "  codeweave . --lang python --tree"
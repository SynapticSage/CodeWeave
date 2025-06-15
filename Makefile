# CodeWeave Makefile
# Provides easy installation and management commands

.PHONY: help install install-dev uninstall clean test global-script install-global uninstall-global shell-alias remove-shell-alias

# Default target
help:
	@echo "CodeWeave - Intelligent source code aggregation and AI workflow optimization"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@echo "Installation:"
	@echo "  make setup          - Complete setup (package + global script + g2f alias)"
	@echo "  make setup-basic    - Basic setup (package + global script only)"
	@echo "  make install        - Install CodeWeave package only"
	@echo "  make install-dev    - Install in development mode"
	@echo "  make install-global - Install package + global script (requires sudo)"
	@echo ""
	@echo "Configuration:"
	@echo "  make global-script  - Install global script only (requires sudo)"
	@echo "  make shell-alias    - Add g2f alias to shell config files"
	@echo "  make remove-shell-alias - Remove g2f alias from shell config files"
	@echo ""
	@echo "Maintenance:"
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
	@echo "  g2f <path>                 # Legacy alias (after 'make shell-alias')"

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

# Add g2f alias to shell configuration files
shell-alias:
	@echo "Adding g2f alias to shell configuration files..."
	@if [ -f "$$HOME/.zshrc" ]; then \
		if ! grep -q "alias g2f=" "$$HOME/.zshrc"; then \
			echo "" >> "$$HOME/.zshrc"; \
			echo "# CodeWeave legacy alias" >> "$$HOME/.zshrc"; \
			echo "alias g2f='codeweave'" >> "$$HOME/.zshrc"; \
			echo "✓ Added g2f alias to ~/.zshrc"; \
		else \
			echo "g2f alias already exists in ~/.zshrc"; \
		fi; \
	else \
		echo "~/.zshrc not found, skipping"; \
	fi
	@if [ -f "$$HOME/.bashrc" ]; then \
		if ! grep -q "alias g2f=" "$$HOME/.bashrc"; then \
			echo "" >> "$$HOME/.bashrc"; \
			echo "# CodeWeave legacy alias" >> "$$HOME/.bashrc"; \
			echo "alias g2f='codeweave'" >> "$$HOME/.bashrc"; \
			echo "✓ Added g2f alias to ~/.bashrc"; \
		else \
			echo "g2f alias already exists in ~/.bashrc"; \
		fi; \
	else \
		echo "~/.bashrc not found, skipping"; \
	fi
	@if [ -f "$$HOME/.bash_profile" ]; then \
		if ! grep -q "alias g2f=" "$$HOME/.bash_profile"; then \
			echo "" >> "$$HOME/.bash_profile"; \
			echo "# CodeWeave legacy alias" >> "$$HOME/.bash_profile"; \
			echo "alias g2f='codeweave'" >> "$$HOME/.bash_profile"; \
			echo "✓ Added g2f alias to ~/.bash_profile"; \
		else \
			echo "g2f alias already exists in ~/.bash_profile"; \
		fi; \
	else \
		echo "~/.bash_profile not found, skipping"; \
	fi
	@echo ""
	@echo "✓ Shell aliases configured!"
	@echo "Restart your shell or run 'source ~/.zshrc' or 'source ~/.bashrc' to use 'g2f' command"

# Remove g2f alias from shell configuration files
remove-shell-alias:
	@echo "Removing g2f alias from shell configuration files..."
	@if [ -f "$$HOME/.zshrc" ]; then \
		sed -i.bak '/# CodeWeave legacy alias/,/alias g2f=/d' "$$HOME/.zshrc" && \
		echo "✓ Removed g2f alias from ~/.zshrc"; \
	fi
	@if [ -f "$$HOME/.bashrc" ]; then \
		sed -i.bak '/# CodeWeave legacy alias/,/alias g2f=/d' "$$HOME/.bashrc" && \
		echo "✓ Removed g2f alias from ~/.bashrc"; \
	fi
	@if [ -f "$$HOME/.bash_profile" ]; then \
		sed -i.bak '/# CodeWeave legacy alias/,/alias g2f=/d' "$$HOME/.bash_profile" && \
		echo "✓ Removed g2f alias from ~/.bash_profile"; \
	fi
	@echo "✓ Shell aliases removed! Restart your shell for changes to take effect."

# Complete setup (install + global script + shell alias)
setup: clean install-global shell-alias
	@echo "✓ Complete CodeWeave setup finished!"
	@echo ""
	@echo "Try it out:"
	@echo "  codeweave . --lang python --tree"
	@echo "  g2f . --lang python --tree"

# Complete setup without shell alias
setup-basic: clean install-global
	@echo "✓ Basic CodeWeave setup finished!"
	@echo ""
	@echo "Try it out:"
	@echo "  codeweave . --lang python --tree"
# Fixing Python 3.12+ Compatibility Issues

## Problem

Python 3.12+ removed `distutils` from the standard library. Some older packages (like numpy 1.24.3) require it to build.

## Solution

Updated `requirements.txt` to use:
- `numpy>=1.26.0` - Compatible with Python 3.12+
- `setuptools>=65.0.0` - Provides distutils for any packages that still need it

## Installation Steps

```bash
# Make sure you're in backend directory
cd /c/Users/DavidM/costmelt/backend

# Activate virtual environment
source .venv/Scripts/activate

# Upgrade pip first
python -m pip install --upgrade pip

# Install setuptools first (provides distutils)
pip install setuptools>=65.0.0

# Now install requirements
pip install -r requirements.txt
```

## Alternative: Use Python 3.11

If you prefer to use Python 3.11 (which includes distutils):

```bash
# Create venv with Python 3.11
python3.11 -m venv .venv

# Activate
source .venv/Scripts/activate

# Install requirements
pip install -r requirements.txt
```

## Verify Installation

```bash
# Check numpy version
python -c "import numpy; print(numpy.__version__)"

# Should show: 1.26.0 or higher
```


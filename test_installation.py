"""
Test script to verify installation and basic functionality.
"""
import sys


def test_imports():
    """Test that all required packages are installed."""
    print("Testing imports...")
    
    packages = [
        ('PyQt6', 'PyQt6'),
        ('pyqtgraph', 'pyqtgraph'),
        ('numpy', 'numpy'),
        ('scipy', 'scipy'),
        ('pandas', 'pandas'),
    ]
    
    optional_packages = [
        ('h5py', 'h5py (optional, for HDF5 support)'),
    ]
    
    all_good = True
    
    for module_name, display_name in packages:
        try:
            __import__(module_name)
            print(f"✓ {display_name}")
        except ImportError:
            print(f"✗ {display_name} - NOT INSTALLED")
            all_good = False
    
    for module_name, display_name in optional_packages:
        try:
            __import__(module_name)
            print(f"✓ {display_name}")
        except ImportError:
            print(f"  {display_name} - not installed (optional)")
    
    return all_good


def test_modules():
    """Test that application modules can be imported."""
    print("\nTesting application modules...")
    
    modules = [
        'src.models.sensor_data',
        'src.models.annotation',
        'src.utils.data_loader',
        'src.utils.signal_processing',
        'src.utils.export',
        'src.widgets.timeseries_widget',
        'src.widgets.fft_widget',
        'src.widgets.spectrogram_widget',
        'src.widgets.parameter_panel',
        'src.widgets.annotation_panel',
        'src.main_window',
    ]
    
    all_good = True
    
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name}")
        except ImportError as e:
            print(f"✗ {module_name} - ERROR: {e}")
            all_good = False
    
    return all_good


def main():
    """Run all tests."""
    print("=" * 60)
    print("Sensor Data Annotation Tool - Installation Test")
    print("=" * 60)
    print()
    
    imports_ok = test_imports()
    modules_ok = test_modules()
    
    print()
    print("=" * 60)
    
    if imports_ok and modules_ok:
        print("✓ All tests passed!")
        print()
        print("You're ready to use the Sensor Data Annotation Tool!")
        print()
        print("Next steps:")
        print("1. Generate sample data: python generate_sample_data.py")
        print("2. Run the application: python src/main.py")
        print("3. See GETTING_STARTED.md for usage instructions")
        return 0
    else:
        print("✗ Some tests failed.")
        print()
        print("Please install missing dependencies:")
        print("  pip install -r requirements.txt")
        return 1


if __name__ == '__main__':
    sys.exit(main())

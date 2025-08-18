"""Test if the integration can be imported."""

print("HTTP Request integration is being loaded...")

try:
    from . import config_flow
    print("config_flow imported successfully")
except Exception as e:
    print(f"Error importing config_flow: {e}")

try:
    from . import sensor  
    print("sensor imported successfully")
except Exception as e:
    print(f"Error importing sensor: {e}")

print("Basic imports completed")
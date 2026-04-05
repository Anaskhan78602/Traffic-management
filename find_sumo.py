import os
import sys
import subprocess

def find_sumo():
    """Find SUMO installation on your system"""
    
    # Check common locations
    possible_paths = [
        "/Applications/SUMO.app",
        "/Applications/SUMO GUI.app",
        "/Applications/SUMO sumo-gui.app",
        "/usr/local/share/sumo",
        "/opt/homebrew/share/sumo",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            # Check for tools directory
            tools_path = None
            for subpath in ["tools", "Contents/MacOS/tools"]:
                test_path = os.path.join(path, subpath)
                if os.path.exists(test_path):
                    tools_path = test_path
                    break
            
            if tools_path:
                print(f"Found SUMO at: {path}")
                print(f"Tools at: {tools_path}")
                return path, tools_path
    
    # Try to find sumo binary
    try:
        result = subprocess.run(['which', 'sumo'], capture_output=True, text=True)
        if result.returncode == 0:
            sumo_bin = result.stdout.strip()
            sumo_dir = os.path.dirname(os.path.dirname(sumo_bin))
            tools_path = os.path.join(sumo_dir, "share", "sumo", "tools")
            if os.path.exists(tools_path):
                return sumo_dir, tools_path
    except:
        pass
    
    return None, None

if __name__ == "__main__":
    sumo_dir, tools_path = find_sumo()
    if sumo_dir:
        print(f"\n✅ SUMO found!")
        print(f"   Install dir: {sumo_dir}")
        print(f"   Tools dir: {tools_path}")
        
        # Set environment for this script
        if tools_path and tools_path not in sys.path:
            sys.path.insert(0, tools_path)
        
        try:
            import traci
            print(f"   TraCI version: {traci.getVersion()}")
        except:
            print("   TraCI not available - install with: pip3 install traci")
    else:
        print("\n❌ SUMO not found")
        print("Please install SUMO or use the mock simulator")

import os
import sys
import winreg

def setup_registry():
    matlab_exe = r"E:\Program Files\MATLAB\R2026a\bin\matlab.exe"
    
    # 1. Associate .m with MATLAB.m
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.m") as k:
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "MATLAB.m")
        
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\MATLAB.m") as k:
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "MATLAB Code File")
        
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\MATLAB.m\DefaultIcon") as k:
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f'"{matlab_exe}",0')
        
    open_cmd = f'"{matlab_exe}" -nosplash -r "edit(\'%1\')"'
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\MATLAB.m\shell\open\command") as k:
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, open_cmd)
        
    # Also register Run with MATLAB
    run_cmd = f'"{matlab_exe}" -nosplash -r "run(\'%1\')"'
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\MATLAB.m\shell\run\command") as k:
        winreg.SetValueEx(k, "", 0, winreg.REG_SZ, run_cmd)

    print("[SUCCESS] Windows Registry updated: .m files associated with MATLAB R2026a")

def create_desktop_files():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    sim_dir = r"C:\Users\user\.gemini\antigravity\scratch\StarshipV3_GNC_Simulation"
    matlab_exe = r"E:\Program Files\MATLAB\R2026a\bin\matlab.exe"
    
    # 1. Desktop .m file
    m_path = os.path.join(desktop, "Starship_Flight14_Simulation.m")
    m_content = '''%% STARSHIP FLIGHT 14 REALISTIC MISSION SIMULATION LAUNCHER
% SpaceX Starship Flight 14 Dual-Vehicle Parallel GNC Simulation
% Autonomous Ascent, MECO, Hot-Staging, Orbital Insertion & GNC Execution

clear; clc; close all;
fprintf('=====================================================================\\n');
fprintf('   SPACEX STARSHIP FLIGHT 14 REAL-TIME MISSION SIMULATOR (MATLAB)    \\n');
fprintf('=====================================================================\\n');

sim_dir = 'C:\\Users\\user\\.gemini\antigravity\\scratch\\StarshipV3_GNC_Simulation';
if exist(sim_dir, 'dir')
    cd(sim_dir);
    if exist(fullfile(sim_dir, 'src'), 'dir')
        addpath(fullfile(sim_dir, 'src'));
    end
    fprintf('[INFO] Working directory set to: %s\\n', sim_dir);
    fprintf('[INFO] Initiating MasterAscentSimulator...\\n\\n');
    MasterAscentSimulator;
else
    error('Simulation directory not found at: %s', sim_dir);
end
'''
    with open(m_path, "w", encoding="utf-8") as f:
        f.write(m_content)
    print(f"[SUCCESS] Created MATLAB .m script at: {m_path}")
    
    # 2. Desktop .bat launcher
    bat_path = os.path.join(desktop, "Run_Starship_Simulation.bat")
    bat_content = f'''@echo off
title SpaceX Starship Flight 14 MATLAB Simulation
echo =====================================================================
echo  SPACEX STARSHIP FLIGHT 14 REALISTIC MISSION SIMULATION (MATLAB)
echo =====================================================================
echo Launching MATLAB R2026a and running Flight 14 GNC Simulation...
"{matlab_exe}" -nosplash -r "cd('{sim_dir}'); addpath('src'); MasterAscentSimulator;"
'''
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat_content)
    print(f"[SUCCESS] Created .bat launcher at: {bat_path}")

    # 3. Create Windows Shortcut (.lnk) with official MATLAB icon
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut_path = os.path.join(desktop, "Launch Starship Simulation in MATLAB.lnk")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = matlab_exe
        shortcut.Arguments = f'-nosplash -r "cd(\'{sim_dir}\'); addpath(\'src\'); MasterAscentSimulator;"'
        shortcut.WorkingDirectory = sim_dir
        shortcut.IconLocation = f"{matlab_exe}, 0"
        shortcut.Description = "SpaceX Starship Flight 14 MATLAB GNC Simulation"
        shortcut.save()
        print(f"[SUCCESS] Created Windows Desktop Shortcut (.lnk) at: {shortcut_path}")
    except Exception as e:
        # Fallback using PowerShell if pywin32 is not installed
        ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{desktop}\\Launch Starship Simulation in MATLAB.lnk")
$Shortcut.TargetPath = "{matlab_exe}"
$Shortcut.Arguments = "-nosplash -r `"cd('{sim_dir}'); addpath('src'); MasterAscentSimulator;`""
$Shortcut.WorkingDirectory = "{sim_dir}"
$Shortcut.IconLocation = "{matlab_exe},0"
$Shortcut.Description = "SpaceX Starship Flight 14 MATLAB GNC Simulation"
$Shortcut.Save()
'''
        import subprocess
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
        print(f"[SUCCESS] Created Windows Desktop Shortcut (.lnk) via PowerShell at: {desktop}\\Launch Starship Simulation in MATLAB.lnk")

if __name__ == "__main__":
    setup_registry()
    create_desktop_files()

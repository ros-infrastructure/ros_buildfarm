@{
# pinned and checksum verified, like the Pixi installation in ros2/ci
pixi_version = '0.78.0'
pixi_sha256 = '0655d6e11aa1dae56067f266d48b3c5815c02ed0031d5f3e96a1b0b81e1555b4'
}@
# Pixi needs the Visual C++ runtime
RUN powershell -NoProfile -Command "irm https://aka.ms/vs/17/release/vc_redist.x64.exe -OutFile vc_redist.x64.exe"
RUN vc_redist.x64.exe /install /quiet /norestart

# Install a pinned and checksum-verified version of Pixi
RUN powershell -NoProfile -Command "irm https://github.com/prefix-dev/pixi/releases/download/v@(pixi_version)/pixi-x86_64-pc-windows-msvc.zip -OutFile pixi-x86_64-pc-windows-msvc.zip"
RUN powershell -NoProfile -Command "if ((Get-FileHash pixi-x86_64-pc-windows-msvc.zip -Algorithm SHA256).Hash -ne '@(pixi_sha256)') { exit 1 }"
RUN powershell -NoProfile -Command "Expand-Archive -Path pixi-x86_64-pc-windows-msvc.zip -DestinationPath (Join-Path $Env:USERPROFILE\.pixi 'bin') -Force"
RUN powershell -NoProfile -Command "$bindir = Join-Path $Env:USERPROFILE\.pixi 'bin' ; $pathkey = (Get-Item -Path 'HKCU:').OpenSubKey('Environment', $true) ; $oldpath = $pathkey.GetValue('PATH', $null, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames) ; $pathkey.SetValue('PATH', \"$bindir;$oldpath\", [Microsoft.Win32.RegistryValueKind]::String)"

RUN pixi init --channel conda-forge --platform win-64 C:\pixi_ws
WORKDIR C:\pixi_ws

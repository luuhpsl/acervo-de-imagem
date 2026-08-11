Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

pluginDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonScript = pluginDir & "\auth_server_plugin.py"

cmd = "cmd.exe /c cd /d """ & pluginDir & """ && (py -3 """ & pythonScript & """ || python """ & pythonScript & """)"
shell.Run cmd, 0, False

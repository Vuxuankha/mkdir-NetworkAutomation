Option Explicit
Dim shell, fso, base, pyw, cmd
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
pyw = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python313\pythonw.exe"
If Not fso.FileExists(pyw) Then pyw = "pythonw.exe"
cmd = Chr(34) & pyw & Chr(34) & " " & Chr(34) & base & "\NetworkAutomation.pyw" & Chr(34)
shell.CurrentDirectory = base
shell.Run cmd, 0, False

@echo off
for %%f in (*.gim) do (
    gimconv.exe "%%f" -o "%%~nf.png"
)
pause
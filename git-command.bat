@echo off
REM List all new/modified files
for /f "tokens=2*" %%i in ('git status --short') do (
    echo Committing %%i
    git add %%i
    git commit -m "File: %%i" %%i
)

REM Push changes to remote
git push
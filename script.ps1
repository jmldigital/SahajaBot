# Install the Posh-SSH module if not installed
if (-not (Get-Module -Name Posh-SSH -ListAvailable)) {
    Install-Module -Name Posh-SSH -Force -AllowClobber
}

# Получение пути к текущей директории, где находится скрипт
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Создание абсолютного пути к файлу .env
$envPath = Join-Path $scriptPath ".env"

# Получение содержимого файла .env
$envContent = Get-Content -Path $envPath -Raw

# Разбивка содержимого файла .env на строки
$envLines = $envContent -split "`r`n"

# Создание хеш-таблицы для хранения значений
$envVariables = @{}

# Обработка каждой строки файла .env
foreach ($line in $envLines) {
    # Разбивка строки на ключ и значение
    $key, $value = $line -split '=', 2

    # Добавление пары ключ-значение в хеш-таблицу
    $envVariables[$key] = $value
}

# Использование значений из файла .env
$remoteHost = $envVariables["REMOTE_HOST"]
$remoteUser = $envVariables["REMOTE_USER"]
$remotePassword = $envVariables["REMOTE_PASSWORD"]

# SSH Connection
$secpasswd = ConvertTo-SecureString $remotePassword -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($remoteUser, $secpasswd)
$session = New-SSHSession -ComputerName $remoteHost -Credential $credential

# Remote Commands
$commands = @(
    "cd bot",
    "pkill screen",
    "screen -dmS new_session_name bash",
    "screen -S new_session_name -X exec bash -c 'cd bot && source env/bin/activate && python main.py'",
    "screen -list"
)

foreach ($command in $commands) {
    $result = Invoke-SSHCommand -SessionId $session.SessionId -Command $command
    if ($result.ExitStatus -ne 0) {
        Write-Host "Command failed: $($command)"
        Write-Host "Exit Status: $($result.ExitStatus)"
    }
}

# Отображение информации о сессии
$sessionInfo = $result.Output | Out-String
Write-Host "Session Information:"
Write-Host $sessionInfo

# Отсоединение от сессии не выполняется, чтобы скрипт продолжал работать

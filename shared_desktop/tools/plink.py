import pexpect


# Создание SSH-сеанса
ssh_session = pexpect.spawn(
    "ssh -oKexAlgorithms=diffie-hellman-group1-sha1 "
    "-oHostKeyAlgorithms=+ssh-dss itc@192.168.45.13"
)

# Ожидание запроса пароля
ssh_session.expect("password:")

# Ввод пароля
ssh_session.sendline("level1NN")

# Ожидание завершения команды
ssh_session.expect("ITC-2")

# Вывод результатов
print(ssh_session.before.decode())
print(ssh_session.after.decode())

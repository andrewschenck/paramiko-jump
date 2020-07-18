"How do I use paramiko to SSH to a remote host while proxying through a jump host? Also, my jump host requires multi-factor authentication!"

This seems to be a surprisingly common problem with a lot of not-very-working solutions. I figured I'd share my tested, working solution with the world.


```


##
# Test
##
if __name__ == '__main__':

    from jump import SSHJumpClient
    
    
    jump_host_example = 'jump-host'
    target_host_example = 'target-host'

    username = input(f'{target_host_example} Username: ')
    password = getpass(f'{target_host_example} Password: ')

    ssh = SSHJumpClient(jump_host=jump_host_example)
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=target_host_example,
        username=username,
        password=password,
    )

    stdin, stdout, stderr = ssh.exec_command('show version')
    print(stdout.read())
    
```

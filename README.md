# Installation notes

## Emacs
    sudo snap install emacs --classic

## Conda

See: https://conda.io/projects/conda/en/latest/user-guide/install/linux.html

    diff Miniconda3-latest-Linux-x86_64.sh.sha256sum.actual Miniconda3-latest-Linux-x86_64.sh.sha256sum.expected
    bash Miniconda3-latest-Linux-x86_64.sh
    conda config --set auto_activate_base false

## Docker

See: https://conda.io/projects/conda/en/latest/user-guide/install/linux.html, and
https://docs.docker.com/engine/install/linux-postinstall/

    sudo apt-get update
    sudo apt-get install \
         apt-transport-https \
	 ca-certificates \
	 curl \
	 gnupg \
	 lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo \
        "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install docker-ce docker-ce-cli containerd.io
    sudo docker run hello-world
    sudo groupadd docker
    sudo usermod -aG docker $USER
    newgrp docker 
    docker run hello-world
    sudo systemctl enable docker.service
    sudo systemctl enable containerd.service

## DTrace

See: http://dtrace.org/blogs/about/

    sudo apt install systemtap-sdt-dev

## Sysdig
    sudo apt install sysdig

# Testing notes

## conda

See: https://conda.io/projects/conda/en/latest/index.html
See: https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html

## strace

See: https://man7.org/linux/man-pages/man1/strace.1.html

## dtrace

See: http://dtrace.org/blogs/about/

## sysdig

See: https://github.com/draios/sysdig

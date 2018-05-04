Vagrant.configure("2") do |config|
    config.vm.box = "bento/ubuntu-18.04"

    config.vm.network "forwarded_port", guest: 22, host: 2200, id: "ssh", auto_correct: true
    config.vm.network "forwarded_port", guest: 5432, host: 5432, id: "postgresql"
    config.vm.network "forwarded_port", guest: 8000, host: 8000

    config.vm.provider "virtualbox" do |vb|
        vb.memory = "1024"
    end
end

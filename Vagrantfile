require "yaml"

# Load up our vagrant config files -- vagrantconfig.yaml first
_config = YAML.load(File.open(File.join(File.dirname(__FILE__),
                    "vagrantconfig.yaml"), File::RDONLY).read)

# Local-specific/not-git-managed config -- vagrantconfig_local.yaml
begin
    extra = YAML.load(File.open(File.join(File.dirname(__FILE__),
                      "vagrantconfig_local.yaml"), File::RDONLY).read)
    if extra
        _config.merge!(extra)
    end
rescue Errno::ENOENT # No vagrantconfig_local.yaml found -- that's OK; just
                     # use the defaults.
end

CONF = _config
MOUNT_POINT = '/home/vagrant/kitsune'

Vagrant.configure(2) do |config|
    config.vm.box = "ubuntu/trusty64"

    config.vm.network "forwarded_port", guest:8000, host:8000

    config.vm.network "private_network", ip: "33.33.33.77"

    config.vm.synced_folder ".", "/vagrant", disabled: true
    config.vm.synced_folder ".", MOUNT_POINT

    config.vm.provider "virtualbox" do |vb|
        vb.memory = CONF['memory']
    end

    config.vm.provision "shell", path: "bin/vagrant_provision.sh"
end

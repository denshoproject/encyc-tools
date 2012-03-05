# source: therealkatie.net/blog/2011/nov/28/katie-finally-talks-about-her-fabfiles/

from fabric.api import run, sudo, hosts, settings, abort, warn, cd, local, put, get
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, contains, sed, append
from fabric.operations import prompt

import string, random

PACKAGES = ('ssh', 'ufw', 'mg', 'curl', 'wget',)

def pre_setup():
    print 'Setting up VirtualBox guest.'
    print 'Customize vanilla-deb6 before continuing.'
    print '  - Make a clone of vanilla-deb6.'
    print '  - Boot guest.'
    print '  - Login as root.'
    print '  - [Optional] Change static IP address:'
    print '      # vi /etc/network/interfaces'
    print '  - Add login user to sudoers.'
    print '  - Install openssh (generates unique keys for the VM):'
    print '      # apt-get install ssh'
    print '  - Logout.'
    prompt('DONE?', validate='y')

def root_password():
    print 'Changing root password.'
    sudo('passwd root')
    
def hostname():
    print 'Changing hostname.'
    hostname = prompt('Hostname:', validate=r'^\w+$')
    sudo('echo "%s" > /etc/hostname' % hostname)
    sudo('hostname -F /etc/hostname')
    sed('/etc/hosts', '127.0.1.1\tdebian', '127.0.1.1\t%s' % hostname, use_sudo=True)

def user_add(user):
    sudo('useradd %s' % user)
    sudo('echo "%s ALL=(ALL) ALL" >> /etc/sudoers' % user)
    password = prompt('Password for %s' % user,
                      validate=r'^\w+$')
    sudo('echo "%s:%s" | chpasswd' % (user, password))
    print "Password for %s is %s" % (user, password)

def apt_install():
    for p in PACKAGES:
        sudo('apt-get -y install %s' % p)

def aptup():
    sudo('apt-get update && apt-get upgrade')

def ssh_setup():
    # root login off
    sed('/etc/ssh/sshd_config', 'PermitRootLogin yes', 'PermitRootLogin no', use_sudo=True)
    # UseDNS
    if not contains('/etc/ssh/sshd_config', 'UseDNS'):
        sudo('echo "" >> /etc/ssh/sshd_config')
        sudo('echo "UseDNS no" >> /etc/ssh/sshd_config')
    # AllowUsers
    if not contains('/etc/ssh/sshd_config', 'AllowUsers'):
        sudo('echo "" >> /etc/ssh/sshd_config')
        users = prompt('AllowUsers:')
        sudo('echo "AllowUsers %s" >> /etc/ssh/sshd_config' % users)
    # restart
    sudo('/etc/init.d/ssh restart')


MW_PATH = '/opt/mediawiki-1.18.1-0/apps/mediawiki/htdocs'
MW_LOCALSETTINGS = '%s/LocalSettings.php' % MW_PATH
MW_EXTENSIONS_PATH = '%s/extensions' % MW_PATH

def mediawiki_setup():
    print('------------------------------------------------------------------------') 
    # Make sure port 80 is open
    sudo('ufw allow 80/tcp')
    # Install
    print('Installing  Bitnami MediaWiki')
    version = '1.18.1-0'
    filename = 'bitnami-mediawiki-%s-linux-installer.bin' % version
    url = 'http://bitnami.org/files/stacks/mediawiki/%s/%s' % (version, filename)
    run('wget %s' % url)
    run('chmod +x %s' % filename)
    sudo('./%s' % filename)

def mediawiki_extensions():
    ls = MW_LOCALSETTINGS
    print('------------------------------------------------------------------------') 
    print('Extension:WikiEditor')
    if not contains(ls, 'WikiEditor.php'):
        append(ls, '', use_sudo=True);
        append(ls, '# WikiEditor.php', use_sudo=True);
        append(ls, 'require_once("$IP/extensions/WikiEditor/WikiEditor.php");', escape=False, use_sudo=True);
        append(ls, "$wgDefaultUserOptions['usebetatoolbar'] = 1;", escape=False, use_sudo=True);
        append(ls, "$wgDefaultUserOptions['usebetatoolbar-cgd'] = 1;", escape=False, use_sudo=True);
        append(ls, "$wgDefaultUserOptions['wikieditor-preview'] = 1;", escape=False, use_sudo=True);
    with cd(MW_EXTENSIONS_PATH):
        print('------------------------------------------------------------------------')
        print('Extension:ParserFunctions')
        if not exists('%s/ParserFunctions' % MW_EXTENSIONS_PATH):
            filename = 'ParserFunctions-MW1.18-r98766'
            sudo('wget http://upload.wikimedia.org/ext-dist/%s.tar.gz' % filename)
            sudo('tar xf %s.tar.gz' % filename)
            sudo('rm -Rf %s.tar.gz' % filename)
        if not contains(ls, 'ParserFunctions.php'):
            append(ls, '', use_sudo=True);
            append(ls, '# ParserFunctions.php', use_sudo=True);
            append(ls, 'require_once("$IP/extensions/ParserFunctions/ParserFunctions.php");', use_sudo=True);
            append(ls, '$wgPFEnableStringFunctions = true;', use_sudo=True);
        print('------------------------------------------------------------------------')
        print('Extension:Cite')
        if not exists('%s/Cite' % MW_EXTENSIONS_PATH):
            filename = 'Cite-MW1.18-r98759'
            sudo('wget http://upload.wikimedia.org/ext-dist/%s.tar.gz' % filename)
            sudo('tar xf %s.tar.gz' % filename)
            sudo('rm -Rf %s.tar.gz' % filename)
        if not contains(ls, 'Cite.php'):
            append(ls, '', use_sudo=True);
            append(ls, '# Cite', use_sudo=True);
            append(ls, 'require_once("$IP/extensions/Cite/Cite.php");', use_sudo=True);
        print('------------------------------------------------------------------------')
        print('Extension:Cite/Special:Cite.php')
        if not contains(ls, 'SpecialCite.php'):
            append(ls, '', use_sudo=True);
            append(ls, '# SpecialCite', use_sudo=True);
            append(ls, 'require_once("$IP/extensions/Cite/SpecialCite.php");', use_sudo=True);
        print('------------------------------------------------------------------------')
        print('Permissions')
        sudo('chown -R root.daemon *')
        # recursively chmod directories 755, files 644
        sudo('for i in `find . -type d`; do  chmod 755 $i; done')
        sudo('for i in `find . -type f`; do  chmod 644 $i; done')

def bootstrap():
    pre_setup()
    hostname()
    root_password()
    ssh_setup()
    aptup()
    apt_install()
    #mediawiki_setup()

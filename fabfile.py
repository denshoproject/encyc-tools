# source: therealkatie.net/blog/2011/nov/28/katie-finally-talks-about-her-fabfiles/

import codecs
import random
import string

from fabric.api import run, sudo, hosts, settings, abort, warn, cd, local, put, get, env, open_shell
from fabric.contrib.console import confirm
from fabric.contrib.files import exists, contains, sed, append
from fabric.operations import prompt

PACKAGES = ['ssh', 'ufw', 'mg', 'curl', 'wget', 'htop', 'ack-grep', 'elinks',
            'git-core', 'subversion', 'python-pip',
            'imagemagick',]

def pre_setup():
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



# PUPPET ===============================================================

PUPPET_MASTER_IP = '10.0.1.24'
PUPPET_PORT = '8140'

def puppet_master_setup():
    # install packages
    for p in ['git', 'puppet', 'puppetmaster',]:
        sudo('apt-get -y install %s' % p)
    ## clone configs
    #with('/etc'):
    #    sudo('git clone USER@SERVER:/var/git/REPO.git ./puppet')
    # 
    
def puppet_master_pull():
    with('/etc/puppet'):
        sudo('git fetch')
        sudo('git pull')

def puppet_client_setup():
    # install packages
    for p in ['puppet',]:
        sudo('apt-get -y install %s' % p)
    # add puppet to /etc/hosts
    if not contains('/etc/hosts', 'puppetmaster'):
        append(ls, '', use_sudo=True);

def _puppet_master_allowtcp(client_ip):
    sudo('ufw allow proto tcp from %s to any port %s' % (client_ip, PUPPET_PORT))

def _puppet_client_request():
    sudo('ufw allow proto tcp from %s, to any port %s' % (PUPPET_MASTER_IP, PUPPET_PORT))
    sudo('puppetd --server puppetmaster --waitforcert 60 --test &&')

def _puppet_master_sign():
    sudo('puppetca --list')
    prompt('Client Hostname?', key='client_hostname')
    sudo('puppetca --sign %s' % client_hostname)

def puppet_register():
    prompt('Client IP?', key='client_ip')
    _puppet_master_allowtcp(env.client_ip)
    _puppet_client_request()
    _puppet_master_sign()



# MEDIAWIKI ============================================================

BITNAMI_PATH = '/opt/mediawiki-1.18.1-0'
MW_PATH = '%s/apps/mediawiki/htdocs' % BITNAMI_PATH
MW_LOCALSETTINGS = '%s/LocalSettings.php' % MW_PATH
MW_EXTENSIONS_PATH = '%s/extensions' % MW_PATH
MW_VERSION = '1.18.1-0'
MW_FILENAME = 'bitnami-mediawiki-%s-linux-installer.bin' % MW_VERSION

def mw_setup():
    print('------------------------------------------------------------------------') 
    # Make sure port 80 is open
    sudo('ufw allow 80/tcp')
    # Install
    print('Installing  Bitnami MediaWiki')
    url = 'http://bitnami.org/files/stacks/mediawiki/%s/%s' % (MW_VERSION,
                                                               MW_FILENAME)
    if not exists('./%s' % MW_FILENAME):
        run('wget %s' % url)
        run('chmod +x %s' % MW_FILENAME)
    sudo('./%s' % MW_FILENAME)

def mw_extensions():
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
    print('------------------------------------------------------------------------') 
    print('Miscellaneous Settings')
    if not contains(ls, '$wgFileExtensions[]'):
        append(ls, '', use_sudo=True);
        append(ls, '# SVG graphics', use_sudo=True);
        append(ls, "$wgFileExtensions[] = 'svg';", escape=False, use_sudo=True);
        append(ls, "$wgAllowTitlesInSVG = true;", escape=False, use_sudo=True);
        append(ls, "$wgSVGConverter = 'ImageMagick';", escape=False, use_sudo=True);

USER_CONFIG = """# -*- coding: utf-8  -*-
family = '%(family)s'
mylang = 'en'
usernames = {}
usernames['%(family)s'] = {}
usernames['%(family)s']['en'] = u'%(botname)s'
authenticate['%(hostname)s'] = ('%(botname)s','%(botpass)s')
sysopnames['%(family)s']['en']='%(sysopname)s'"""

def mw_bot_setup():
    print('------------------------------------------------------------------------')
    print('git clone gjost@jostwebwerks.com:/var/git/densho-wikitools.git')
    src = 'http://svn.wikimedia.org/svnroot/pywikipedia/trunk/pywikipedia/'
    print('svn checkout %s ./pywikipedia' % src)
    # user-config.py
    prompt(' Wiki hostname?', key='hostname')
    prompt('   Wiki family?', key='family')
    prompt('Sysop username?', key='sysopname')
    prompt('  Bot username?', key='botname')
    prompt('  Bot password?', key='botpass')
    user_config = USER_CONFIG % {
        'hostname':unicode(env.hostname),
        'family':unicode(env.family),
        'sysopname':unicode(env.sysopname),
        'botname':unicode(env.botname),
        'botpass':unicode(env.botpass),}
    print('user-config.py:')
    print('----------------------------------------')
    print(user_config)
    print('----------------------------------------')
    print('- Login to %s' % env.hostname)
    print('- cd to pywikipedia')
    print('- vi user-config.py')
    print('- python generate_family_file.py')

def mw_teardown():
    print('------------------------------------------------------------------------')
    with cd(BITNAMI_PATH):
        sudo('./uninstall')
    #run('rm %s' % MW_FILENAME)
    # Close port 80
    sudo('ufw delete allow 80/tcp')

def bootstrap():
    pre_setup()
    hostname()
    root_password()
    ssh_setup()
    aptup()
    apt_install()
    #mw_setup()
    #mw_extensions()
    #mw_pywikibot()
    

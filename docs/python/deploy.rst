Building a deployable plugin
############################

Once development is finished it's time to package the code into a deployable package. Before this command a working
pgp code signing key must be setup on the computer. The name and email must match the metadata ``author`` and ``author_email`` specified in setup.py.

Setting up a key
================

You can safely skip this step if you already have a pgp-key setup on your computer.

::

  gpg --gen-key

This will take you through a few questions that will configure your keys.

::

  Please select what kind of key you want: (1) RSA and RSA (default)
  What keysize do you want? 4096
  Key is valid for? 0
  Is this correct? y
  Real name: Enter the same name as in setup.py
  Email address: Enter the same email as in setup.py
  Comment:
  Change (N)ame, (C)omment, (E)mail or (O)kay/(Q)uit? O
  Enter passphrase: Enter a secure passphrase here (upper & lower case, digits, symbols)

Build the plugin
================

To build the package use the ``build-plugin`` command to tellstick.sh

::

  ./tellstick.sh build-plugin [path-to-plugin]

Replace `[path-to-plugin]` with the path to the plugin root folder. During building the plugin
will be signed using your pgp key and if a passphrase has been setup you will be asked for your password.

This will build a .zip file ready to be uploaded to a TellStick.

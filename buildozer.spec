[app]

# (str) Title of your application
title = Snibble

# (str) Package name
package.name = snibble

# (str) Package domain (needed for android/ios packaging)
package.domain = io.github.luprzybyl

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,md

# (str) Application versioning (method 1)
version = 0.1.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,filetype

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (str) Application icon
icon.filename = icon.png

# (list) Permissions
# brak sieci — gra offline, zero uprawnien
android.permissions =

#
# Android specific
#

# (int) Target Android API, should be as high as possible.
#android.api = 34

# (int) Minimum API your APK / AAB will support.
#android.minapi = 21

# (str) Android NDK version to use
#android.ndk = 25b

# (bool) Use --private data storage (default True)
#android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = armeabi-v7a

# (bool) Accept SDK licenses automatically (potrzebne w CI, bez TTY)
android.accept_sdk_license = True

# (bool) Enables Android auto backup and allows cloud backups
#android.allow_backup = True

[buildozer]

# (str) lokalne receptury p4a — vendored kivy z python_depends=['filetype']
# (upstream ciągnie requests -> charset_normalizer z wheel-tagiem Androida
# i wywala build; vendoring = deterministyczny build też w CI)
p4a.local_recipes = recipes

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_as_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
# bin_dir = ./bin

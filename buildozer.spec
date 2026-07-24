[app]

# (str) Title of your application
title = Secret Vault

# (str) Package name
package.name = secretvault

# (str) Package domain (reverse-DNS style)
package.domain = com.nathaniel

# (str) Source code where main.py lives
source.dir = .

# (list) Source files to include
source.include_exts = py,kv,png,jpg,jpeg,gif,webp,mp4,mov,mkv,3gp,ttf,json

# (str) Application versioning
version = 1.0

# (list) Application requirements
# python3/hostpython3 pinned to a real, currently-published patch release.
# A bare "3.11" isn't a valid version for p4a's downloader (it 404s trying
# to fetch it) - it needs the full major.minor.patch string.
# ffpyplayer restored: it's required for Kivy's VideoPlayer to work at all
# on Android; the earlier crashes were Python 3.14 compatibility issues,
# not ffpyplayer itself.
requirements = python3==3.11.15,hostpython3==3.11.15,kivy==2.3.0,plyer,pillow,ffpyplayer

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# ==========================================
# ANDROID SPECIFIC SETTINGS
# ==========================================

# (int) Target Android API, minimum API and NDK/SDK
android.api = 34
android.minapi = 21

# (list) Permissions required for Plyer's FileChooser to grab media
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO

# (list) Supported architectures (Modern 64-bit and standard 32-bit)
android.archs = arm64-v8a, armeabi-v7a

# (bool) Disable Android's automatic cloud/adb backup of app data.
# Prevents Google Drive from backing up the hidden media folder.
android.allow_backup = False

# (bool) Enforce private storage for the app
android.private_storage = True

# (bool) Enable AndroidX support (Crucial for Plyer compatibility on API 34)
android.enable_androidx = True

# (str) Presplash background color (Matches your kv background)
android.presplash_color = #000000

# (str) Format of the release artifact (only applies to `buildozer android
# release`, not the debug build your CI currently runs)
android.release_artifact = apk

[buildozer]

# (int) Log level (2 = debug, best for catching build errors)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
